# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import os
from metaflow import (
    FlowSpec,
    Parameter,
    card,
    current,
    step,
    environment,
    kubernetes,
    pypi,
    nvidia,
)
from metaflow.cards import Markdown

# Set the right GCP project and GCS bucket
GCS_PROJECT_NAME = "your-gcp-project-here"
GCS_BUCKET_NAME = "your-gcs-bucket-here"
# Model blob to be uploaded to GCS
MODEL_STORAGE_PATH = "image_classifier/trained-model-bytes.pth"


class ImageClassifierFlow(FlowSpec):
    # This is an example of a parameter. You can toggle this when you call the flow
    # with python template_flow.py run --offline False
    offline_wandb = Parameter(
        "offline",
        help="Do not connect to W&B servers when training",
        type=bool,
        default=True,
    )

    @pypi(python="3.11.9", packages={"torchvision": "0.19.1"})
    @card(type="default")
    @kubernetes
    @step
    def start(self):
        import torchvision
        import torchvision.transforms as transforms

        # Download and normalize CIFAR10
        print("start step: downloading and normalizing dataset")
        transform = transforms.Compose(
            [
                transforms.ToTensor(),
                transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
            ]
        )

        self.trainset = torchvision.datasets.CIFAR10(
            root="./data", train=True, download=True, transform=transform
        )
        self.testset = torchvision.datasets.CIFAR10(
            root="./data", train=False, download=True, transform=transform
        )
        self.next(self.train)

    # Train the network
    # Keep @nvidia decorator before @step decorator else the flow fails
    @pypi(
        python="3.11.9",
        packages={"torch": "2.4.1", "torchvision": "0.19.1", "mozmlops": "0.1.4"},
    )
    @nvidia
    # @kubernetes
    @card
    @environment(
        vars={
            "WANDB_API_KEY": os.getenv("WANDB_API_KEY"),
            "WANDB_PROJECT": os.getenv("WANDB_PROJECT"),
        }
    )
    @step
    def train(self):
        import torch
        import torch.nn as nn
        import torch.optim as optim
        from image_classifier_model import ImageClassifierModel
        from io import BytesIO
        import wandb
        import os

        tracking_run = {}
        if not self.offline_wandb:
            tracking_run = wandb.init(project=os.getenv("WANDB_PROJECT"))
            wandb_url = tracking_run.get_url()
            current.card.append(Markdown("# Weights & Biases"))
            current.card.append(
                Markdown(f"Your training run is tracked [here]({wandb_url}).")
            )

        device = torch.device("cpu")
        # Check if GPU is available
        if torch.cuda.is_available():
            import os

            print(os.system("nvidia-smi"))
            device = torch.device("cuda")

        print(f"Training on: {device}")

        image_classifier_model = ImageClassifierModel().to(device)

        # Define a Loss function and optimizer
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.SGD(
            image_classifier_model.parameters(), lr=0.001, momentum=0.9
        )

        # Load train data
        batch_size = 4
        trainloader = torch.utils.data.DataLoader(
            self.trainset, batch_size=batch_size, shuffle=True, num_workers=2
        )

        # Start training
        num_epochs = 2
        for epoch in range(num_epochs):  # loop over the dataset multiple times
            running_loss = 0.0
            for i, data in enumerate(trainloader, 0):
                # get the inputs; data is a list of [inputs, labels]
                inputs, labels = data[0].to(device), data[1].to(device)

                # zero the parameter gradients
                optimizer.zero_grad()

                # forward + backward + optimize
                outputs = image_classifier_model(inputs)
                loss = criterion(outputs, labels)
                loss.backward()
                optimizer.step()

                # print statistics
                running_loss += loss.item()
                if i % 2000 == 1999:  # print every 2000 mini-batches
                    print(f"[{epoch + 1}, {i + 1:5d}] loss: {running_loss / 2000:.3f}")
                    # log metrics to wandb
                    wandb.log({"mini-batches": {i + 1}, "loss": {running_loss / 2000}})
                    running_loss = 0.0

        print("Finished Training")
        buffer = BytesIO()
        torch.save(image_classifier_model.state_dict(), buffer)
        self.model_state_dict_bytes = buffer.getvalue()

        if not self.offline_wandb:
            # Save trained model locally and then track it in W&B
            torch.save(image_classifier_model.state_dict(), "./trained_model.pt")
            model_artifact = wandb.Artifact(name="trained_image_classifier", type="model")
            model_artifact.add_file(local_path="./trained_model.pt")
            tracking_run.log_artifact(model_artifact)

        self.next(self.evaluate)

    # Test the model on the test data
    @pypi(
        python="3.11.9",
        packages={
            "torch": "2.4.1",
            "torchvision": "0.19.1",
        },
    )
    @kubernetes
    @step
    def evaluate(self):
        import torch
        from image_classifier_model import ImageClassifierModel
        from io import BytesIO

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Evaluating on: {device}")

        image_classifier_model = ImageClassifierModel().to(device)
        buffer = BytesIO(self.model_state_dict_bytes)
        image_classifier_model.load_state_dict(
            torch.load(buffer, map_location=device, weights_only=True)
        )

        correct = 0
        total = 0

        # load test data
        batch_size = 4
        testloader = torch.utils.data.DataLoader(
            self.testset, batch_size=batch_size, shuffle=False, num_workers=2
        )
        # since we're not training, we don't need to calculate the gradients for our outputs
        with torch.no_grad():
            for data in testloader:
                images, labels = data[0].to(device), data[1].to(device)
                # calculate outputs by running images through the network
                outputs = image_classifier_model(images)
                # the class with the highest energy is what we choose as prediction
                _, predicted = torch.max(outputs.data, 1)
                total += labels.size(0)
                correct += (predicted == labels).sum().item()

        print(
            f"Accuracy of the network on the 10000 test images: {100 * correct // total} %"
        )
        self.next(self.upload_model_to_gcs)

    @pypi(python="3.11.9", packages={"mozmlops": "0.1.4"})
    @kubernetes
    @step
    def upload_model_to_gcs(self):
        from mozmlops.cloud_storage_api_client import CloudStorageAPIClient

        print("Uploading model to gcs")
        # init client
        storage_client = CloudStorageAPIClient(
            project_name=GCS_PROJECT_NAME, bucket_name=GCS_BUCKET_NAME
        )
        storage_client.store(
            data=self.model_state_dict_bytes, storage_path=MODEL_STORAGE_PATH
        )
        self.next(self.end)

    @kubernetes
    @step
    def end(self):
        print(
            f"""
            Flow complete.

            See artifacts at {GCS_BUCKET_NAME}.
            """
        )


if __name__ == "__main__":
    ImageClassifierFlow()
