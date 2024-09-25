import os
from metaflow import (
    FlowSpec,
    IncludeFile,
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

GCS_PROJECT_NAME = "moz-fx-mlops-inference-nonprod"
GCS_BUCKET_NAME = "mf-models-test1"
MODEL_STORAGE_PATH="abhishek-mlops-hackdays/model-bytes.pth"

class ImageClassifier(FlowSpec):

    # This is an example of a parameter. You can toggle this when you call the flow
    # with python template_flow.py run --offline False
    offline_wandb = Parameter(
        "offline",
        help="Do not connect to W&B servers when training",
        type=bool,
        default=True,
    )


    @pypi(python='3.11.9', packages={'torchvision': '0.19.1'})
    @card(type="default")
    @kubernetes
    @step
    def start(self):
        import torchvision
        import torchvision.transforms as transforms

        # Download and normalize CIFAR10
        print(f'start step: downloading and normalizing dataset')
        transform = transforms.Compose(
            [transforms.ToTensor(),
            transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))]
        )
        batch_size = 4
        self.trainset = torchvision.datasets.CIFAR10(root='./data', train=True,
                                                download=True, transform=transform)
        self.testset = torchvision.datasets.CIFAR10(root='./data', train=False,
                                            download=True, transform=transform)
        self.next(self.train)


    # Train the network
    # Keep @nvidia decorator before @step decorator else the flow fails
    @pypi(python='3.11.9', packages={'torch': '2.4.1', 'torchvision': '0.19.1', 'mozmlops': '0.1.4'},)
    @nvidia
    #@kubernetes
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
        import torch.nn.functional as F
        import torch.optim as optim
        from io import BytesIO
        import wandb
        import os

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

        # Define a Convolutional Neural Network
        class Net(nn.Module):
            def __init__(self):
                super().__init__()
                self.conv1 = nn.Conv2d(3, 6, 5)
                self.pool = nn.MaxPool2d(2, 2)
                self.conv2 = nn.Conv2d(6, 16, 5)
                self.fc1 = nn.Linear(16 * 5 * 5, 120)
                self.fc2 = nn.Linear(120, 84)
                self.fc3 = nn.Linear(84, 10)

            def forward(self, x):
                x = self.pool(F.relu(self.conv1(x)))
                x = self.pool(F.relu(self.conv2(x)))
                x = torch.flatten(x, 1) # flatten all dimensions except batch
                x = F.relu(self.fc1(x))
                x = F.relu(self.fc2(x))
                x = self.fc3(x)
                return x

        net = Net().to(device)

        # Define a Loss function and optimizer
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.SGD(net.parameters(), lr=0.001, momentum=0.9)

        # load train data
        batch_size = 4
        trainloader = torch.utils.data.DataLoader(self.trainset, batch_size=batch_size,
                                                shuffle=True, num_workers=2)

        # start training
        num_epochs = 2
        for epoch in range(num_epochs):  # loop over the dataset multiple times
            running_loss = 0.0
            for i, data in enumerate(trainloader, 0):
                # get the inputs; data is a list of [inputs, labels]
                inputs, labels = data[0].to(device), data[1].to(device)

                # zero the parameter gradients
                optimizer.zero_grad()

                # forward + backward + optimize
                outputs = net(inputs)
                loss = criterion(outputs, labels)
                loss.backward()
                optimizer.step()

                # print statistics
                running_loss += loss.item()
                if i % 2000 == 1999:    # print every 2000 mini-batches
                    print(f'[{epoch + 1}, {i + 1:5d}] loss: {running_loss / 2000:.3f}')
                    # log metrics to wandb
                    wandb.log({"mini-batches": {i + 1}, "loss": {running_loss / 2000}})
                    running_loss = 0.0

        print('Finished Training')
        buffer = BytesIO()
        torch.save(net.state_dict(), buffer)
        self.model_state_dict_bytes = buffer.getvalue()
        self.next(self.evaluate)


    # Test the network on the test data
    @pypi(python='3.11.9', packages={'torch': '2.4.1', 'torchvision': '0.19.1',})
    @kubernetes
    @step
    def evaluate(self):
        import torch
        import torch.nn as nn
        import torch.nn.functional as F
        from io import BytesIO

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Evaluating on: {device}")

        # Define a Convolutional Neural Network
        class Net(nn.Module):
            def __init__(self):
                super().__init__()
                self.conv1 = nn.Conv2d(3, 6, 5)
                self.pool = nn.MaxPool2d(2, 2)
                self.conv2 = nn.Conv2d(6, 16, 5)
                self.fc1 = nn.Linear(16 * 5 * 5, 120)
                self.fc2 = nn.Linear(120, 84)
                self.fc3 = nn.Linear(84, 10)

            def forward(self, x):
                x = self.pool(F.relu(self.conv1(x)))
                x = self.pool(F.relu(self.conv2(x)))
                x = torch.flatten(x, 1) # flatten all dimensions except batch
                x = F.relu(self.fc1(x))
                x = F.relu(self.fc2(x))
                x = self.fc3(x)
                return x

        net = Net().to(device)
        buffer = BytesIO(self.model_state_dict_bytes)
        net.load_state_dict(torch.load(buffer, map_location=device, weights_only=True))

        correct = 0
        total = 0

        # load test data
        batch_size = 4
        testloader = torch.utils.data.DataLoader(self.testset, batch_size=batch_size,
                                                shuffle=False, num_workers=2)
        # since we're not training, we don't need to calculate the gradients for our outputs
        with torch.no_grad():
            for data in testloader:
                images, labels = data[0].to(device), data[1].to(device)
                # calculate outputs by running images through the network
                outputs = net(images)
                # the class with the highest energy is what we choose as prediction
                _, predicted = torch.max(outputs.data, 1)
                total += labels.size(0)
                correct += (predicted == labels).sum().item()

        print(f'Accuracy of the network on the 10000 test images: {100 * correct // total} %')
        self.next(self.upload_model_to_gcs)


    @pypi(python='3.11.9', packages={'mozmlops': '0.1.4'})
    @kubernetes
    @step
    def upload_model_to_gcs(self):
        from mozmlops.cloud_storage_api_client import CloudStorageAPIClient

        print(f"Uploading model to gcs")
        # init client
        storage_client = CloudStorageAPIClient(
            project_name=GCS_PROJECT_NAME, bucket_name=GCS_BUCKET_NAME
        )
        storage_client.store(data=self.model_state_dict_bytes, storage_path=MODEL_STORAGE_PATH)
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
    ImageClassifier()
