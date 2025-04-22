# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import os
import torch
import torch.nn as nn
import torch.optim as optim
from image_classifier_model import ImageClassifierModel
from io import BytesIO
import wandb
import torchvision
import torchvision.transforms as transforms


class ImageClassifier():
    # This is an example of a parameter. You can toggle this when you call the flow
    # with python template_flow.py run --offline False
    offline_wandb = False

    def start(self):
        # Download and normalize CIFAR10
        print("downloading and normalizing dataset")

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

        tracking_run = {}
        if not self.offline_wandb:
            wandb_project = os.getenv("WANDB_PROJECT")
            tracking_run = wandb.init(project=wandb_project)
            wandb_url = tracking_run.get_url()
            print(f"Your training run is tracked [here]({wandb_url}).")

        device = torch.device("cpu")
        # Check if GPU is available
        if torch.cuda.is_available():
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
                    if not self.offline_wandb:
                        # log metrics to wandb
                        wandb.log({"mini-batches": {i + 1}, "loss": {running_loss / 2000}})
                    running_loss = 0.0

        print("Finished Training")
        buffer = BytesIO()
        torch.save(image_classifier_model.state_dict(), buffer)
        self.model_state_dict_bytes = buffer.getvalue()

        if not self.offline_wandb:
            # Save trained model locally and then track it in W&B
            print("Tracking trained model via W&B")
            torch.save(image_classifier_model.state_dict(), "./trained_model.pt")
            model_artifact = wandb.Artifact(
                name="trained_image_classifier", type="model"
            )
            model_artifact.add_file(local_path="./trained_model.pt")
            tracking_run.log_artifact(model_artifact)


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

if __name__ == "__main__":
    image_classifier = ImageClassifier()
    image_classifier.start()
