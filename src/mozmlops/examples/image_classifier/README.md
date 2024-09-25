# Example: Image Classifier
**This example is a Metaflow flow that trains an image classifier pytorch model on cloud and tracks the experiments via Weights and Biases. The [original code](https://pytorch.org/tutorials/beginner/blitz/cifar10_tutorial.html) for this example comes from the PyTorch documentation.**

### Flow details
- The training step (`train`) runs on Nvidia cloud
- Rest of the steps run on Kubernetes

### Running this example on cloud
#### Pre-requisites
1. Make sure to follow these [README instructions](../../templates/README.md) to:
    1. Have a User account with Outerbounds
    2. Configure your local machine to run your flows on Outerbounds
    3. Have a User account with Weights & Biases
2. Python installed on your local machine

#### Instructions to run
Run this command on the terminal
   ```
   WANDB_API_KEY=your_wandb_api_key WANDB_PROJECT=your_wandb_project python image_classifier.py --environment=pypi run --offline False
   ```

   Replace `your_wandb_api_key` and `your_wandb_project` with your details.

   You can track the progress of the flow run on Outerbounds UI (see the url in your terminal logs).