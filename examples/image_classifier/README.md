# Example: Image Classifier
**This example is a Metaflow flow that trains an image classifier pytorch model on cloud and uploads the trained model on GCS. It tracks the experiments via Weights and Biases. The [original code](https://pytorch.org/tutorials/beginner/blitz/cifar10_tutorial.html) for this example comes from the PyTorch documentation.**

### Flow details
- The training step (`train`) runs on Nvidia cloud
- Rest of the steps run on Kubernetes

### Running this example on cloud
#### Pre-requisites
1. Follow these [README instructions](../../src/mozmlops/templates/README.md#most-importantly-you-need-an-account-with-outerbounds-do-not-make-this-yourself) to:
    1. Create a User account with Outerbounds if it doesn't exist
    2. Configure your local machine to run your flows on Outerbounds
2. Follow these [README instructions](../../src/mozmlops/templates/README.md#next-tracking-visualizing-and-evaluating-ml-experiments) to:
    1. Have a User account with Weights & Biases
3. Python is installed on your local machine

#### Instructions to run
1. Create a python virtual environment to run the example and activate it
    ```sh
    python -m venv env_example_imageclassifier
    source env_example_imageclassifier/bin/activate
    ```
2. Install the requirements using command:
    ```sh
    pip install -r requirements.example_image_classifier.txt
    ```
2. Set the right GCP project and bucket in the [flow](./image_classifier_flow.py) where you want to upload the trained model to.
3. Run this command on the terminal (replace `your_wandb_api_key` and `your_wandb_project` with your details in this command):
   ```sh
   WANDB_API_KEY=your_wandb_api_key WANDB_PROJECT=your_wandb_project python image_classifier_flow.py --environment=pypi run --offline False
   ```

   You can track the progress of the flow run on Outerbounds UI (see the url in your terminal logs).
4. Once you are done, deactivate the virtual environment
    ```sh
    deactivate
    ```

Please refer to the [Troubleshooting](../../README.troubleshooting.md) guide for the known issues and how to resolve them.
