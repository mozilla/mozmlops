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
    nvct,
)
from metaflow.cards import Markdown
import os, sys, subprocess, importlib, shutil

# Set the right GCP project and GCS bucket
GCS_PROJECT_NAME = "moz-fx-future-products-nonprod"
GCS_BUCKET_NAME = "ksilverstein-0din"
# Model blob to be uploaded to GCS
MODEL_STORAGE_PATH = "image_classifier/trained-model-bytes.pth"


class RuntimeImportHelper:
    @staticmethod
    def sh(cmd):
        print(f"$ {' '.join(cmd)}")
        try:
            return subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
        except subprocess.CalledProcessError as e:
            print(e.output)
            raise

    @staticmethod
    def ensure_cpu_torch(version_torch="2.4.1", version_tv="0.19.1") -> None:
        """
        Ensure CPU-only PyTorch/torchvision are installed before importing torch.
        Forces the official CPU wheel index to avoid accidental CUDA wheels.
        """
        import sys, subprocess, importlib

        try:
            import torch  # already installed?
            # If this torch has *no* CUDA build info, it's CPU-only
            cuda_ver = getattr(getattr(torch, "version", None), "cuda", None)
            if not cuda_ver:
                return
            # If it *does* have a CUDA tag, replace it with CPU wheels.
        except Exception:
            pass

        # Install CPU wheels from the official PyTorch CPU index.
        cpu_index = "https://download.pytorch.org/whl/cpu"
        pkgs = [f"torch=={version_torch}", f"torchvision=={version_tv}"]
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "--index-url", cpu_index] + pkgs)
        importlib.invalidate_caches()

    @staticmethod
    def ensure_cuda_torch(version="2.4.1", tv_version="0.19.1", cuda_tag="cu121"):
        """
        Ensure CUDA-enabled PyTorch and matching torchvision are installed *before* importing them.
        - Installs torch from the official PyTorch CUDA wheel index (e.g., cu121).
        - Installs torchvision from the same index to keep ABI compatible.
        - Purges previously-loaded CPU torch/torchvision modules, then re-imports.
        - Verifies CUDA availability and basic torchvision dataset import.
        """
        import os, sys, subprocess, importlib, shutil

        def sh(cmd):
            print(f"$ {' '.join(cmd)}")
            try:
                return subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
            except subprocess.CalledProcessError as e:
                print(e.output)
                raise

        print("=== GPU/Driver check ===")
        print("NVIDIA_VISIBLE_DEVICES:", os.getenv("NVIDIA_VISIBLE_DEVICES"))
        if shutil.which("nvidia-smi"):
            try:
                print(sh(["nvidia-smi"]))
            except Exception:
                pass
        else:
            print("nvidia-smi not found on PATH (likely no GPU attached)")

        # Install/upgrade torch + torchvision from the CUDA index
        index = f"https://download.pytorch.org/whl/{cuda_tag}"
        pkgs = [f"torch=={version}", f"torchvision=={tv_version}"]
        sh([sys.executable, "-m", "pip", "install", "--upgrade", "--index-url", index] + pkgs)

        # Remove any previously-imported CPU/bad builds from sys.modules
        for m in list(sys.modules):
            if m == "torch" or m.startswith("torch.") or m == "torchvision" or m.startswith("torchvision."):
                del sys.modules[m]
        importlib.invalidate_caches()

        # Import and verify
        import torch  # noqa: E402
        print("torch:", torch.__version__, "torch.version.cuda:", torch.version.cuda)
        print("torch.cuda.is_available():", torch.cuda.is_available())
        if not torch.cuda.is_available():
            raise RuntimeError(
                "CUDA not available in train step. Either no GPU was scheduled, or the node driver "
                "is too old for this wheel. Check nvidia-smi output above."
            )

        # Check torchvision bits (we use for datasets/transforms)
        from torchvision import datasets, transforms  # noqa: F401
        print("torchvision import OK:", tv_version)


class ImageClassifierFlow(FlowSpec):
    # This is an example of a parameter. You can toggle this when you call the flow
    # with python template_flow.py run --offline False
    offline_wandb = Parameter(
        "offline",
        help="Do not connect to W&B servers when training",
        type=bool,
        default=True,
    )

    @pypi(python="3.11.9", packages={})
    @card(type="default")
    @kubernetes
    @step
    def start(self):
        RuntimeImportHelper.ensure_cpu_torch()

        import torch
        assert not torch.cuda.is_available(), "This step should be CPU-only."

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
    @pypi(
        python="3.11.9",
        packages={"mozmlops": "0.1.4"}  # intentionally omit torch/torchvision here
    )
    @nvct
    @card
    @environment(
        vars={
            "WANDB_API_KEY": os.getenv("WANDB_API_KEY"),
            "WANDB_PROJECT": os.getenv("WANDB_PROJECT"),
        }
    )
    @step
    def train(self):
        RuntimeImportHelper.ensure_cuda_torch()

        import torch
        import torch.nn as nn
        import torch.optim as optim
        from image_classifier_model import ImageClassifierModel
        from io import BytesIO
        import wandb
        import os

        assert torch.cuda.is_available(), "This step requires GPU and CUDA isn't installed properly in the container."

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
        self.next(self.evaluate)

    # Test the model on the test data
    @pypi(
        python="3.11.9",
        packages={}
    )
    # Check https://docs.metaflow.org/api/step-decorators/kubernetes for details on @kubernetes decorator
    @kubernetes(cpu=1, memory=4096)
    @step
    def evaluate(self):
        RuntimeImportHelper.ensure_cpu_torch()

        import torch
        assert not torch.cuda.is_available(), "This step should be CPU-only."

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
