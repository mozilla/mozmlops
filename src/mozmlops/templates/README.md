# Training and Deploying Models in The Cloud

So you're a Mozillian with a machine learning model that needs production-grade infrastructure. Excellent! You've found the toolset for this. 

We use deployed Metaflow flows with Outerbounds to do model orchestration, Weights and Biases for experiment evaluation and Ray Serve to run inference servers in production (GKE).

The templates in this repository will help you integrate with them.

## But first...you need some stuff.

### Most importantly, you need an account with Outerbounds. (do not make this yourself).

An admin from Mozilla’s MLOps team needs to set you up with an Outerbounds User account, and also a perimeter if your team doesn’t have that yet. [Here's how Mozillians can get an account](https://mozilla-hub.atlassian.net/wiki/spaces/DATA/pages/708214995/Getting+an+Outerbounds+Account).

Once MLOps comes back to you with a shiny new Outerbounds account, you can sign in [here](https://ui.desertowl.obp.outerbounds.com/dashboard).

Go to [this page right here](https://ui.desertowl.obp.outerbounds.com/dashboard/configure?location=local). You’ll see some instructions. If you installed `mozmlops` you have already installed Outerbounds, so you get to skip that one. 

Back on the [main page](https://ui.desertowl.obp.outerbounds.com/dashboard/runs), look for a dropdown at the top that says “Mozilla/” and then, after it, a perimeter name (probably 'default'). You want to make sure that, if your data has more restricted access than All-Mozilla, you have checked the perimeter name that you received from MLOps. If your data has all-Mozilla access, you can check “default” here.

You should see an instruction to run a command line command that starts with `outerbounds configure`. Copy that whole thing and run it on your command line. What this does, is it makes a `config.json` file located at `~/.metaflowconfig` on your local machine. This is the default configuration for metaflow on your machine now, and unless told otherwise, metaflow flows on your machine will now always run on Outerbounds. 

### Running the template Metaflow flow

1. Install the requirements listed in [`templates/requirements.outerbounds.txt`](requirements.outerbounds.txt) and also add those to your project requirements files.
2. Copy the `template_flow.py` file from this repo into _your_ repo. From there, you can run `python template_flow.py run --offline True`.

> [!TIP]
>The `--offline True` command line argument tells the template flow to not track experiments on W&B.

The Metaflow flow will run internal consistency checks and linting, and then provide a link to track the progress of the flow on our platform, see stderr and stdout, et cetera.

It'll do so on the Outerbounds platform, in the perimeter that you have specified. Perimeters need to be proactively granted access to resources whose access groups are more limited than mozilla-confidential.

### Though these flows are designed to run in the cloud, sometimes you need to run one locally.

Maybe you want to run a quick test on a smaller dataset, or maybe you need to use your employee credentials to spike something before starting the process of getting permissions on your Outerbounds perimeter.

If you want to run the flow _locally_ with _your_ gcloud credentials to test out functionality that depends on permissions that _you_ have but the _perimeter_ doesn't, there are two steps to do that:

1. (You only should ever have to do this once): Add an empty config set to your `.metaflowconfig` directory. This command will do it for you:

```
$echo '{}' > ~/.metaflowconfig/config_local.json
```

2. Run the command to kick off the job with `METAFLOW_PROFILE=local` on the front. For example:

```commandline
$METAFLOW_PROFILE=local python template_flow.py run --offline True
```

Eventually you should see the flow finish with "Task finished successfully." Once you see that, you know you've got a working minimal flow: you're now ready to start putting your model training code _into_ this flow to run it remotely. Comments _inside_ the template file should help you understand where to put that code, and demonstrate some of the tools Metaflow makes available to you.

 ## Next: Tracking, Visualizing, and Evaluating ML Experiments

An admin from Mozilla’s MLOps team needs to set you up with your team on Weights and Biases.[Ask them to add you](https://mozilla-hub.atlassian.net/wiki/spaces/DATA/pages/471010754/Getting+a+Weights+and+Biases+account), and then once they do, you can click through to the invitation to create your Weights and Biases account.

Once you're set up, you're in luck; the `template_flow` already integrates with Weights and Biases for you. 

Note the two environment variables listed at the top of the `train` step:

- The `WANDB_API_KEY` you can get by going to [this page](https://wandb.ai/), once your wandb credentials are set up (see the account provisioning section). Treat this with the sensitive that you would treat any API key. You will see in a later step how to use this string; for now, you can stick this in your local repository’s .env. 

- The `WANDB_PROJECT` is the name of the project that this run is for. If you are deploying a brand new flow that has not appeared on wandb before, you'll need to create a new project for it. Otherwise, you can choose the one for which your teammates have already submitted flows. You can see and create projects for your team at this URL: https://wandb.ai/YOUR_TEAM_NAME_HERE/projects.

You can customize what you send to Weights and Biases as well as the graphs and data that appears there, and the team maintains decent documentation on your customization options. The wandb engineering support team is also incredibly helpful. Talk to MLOps about your problem and they can get you added to our joint channel with wandb where folks are available to help.


When you kick off the flow from your local machine, you can specify the environment variables via our super-advanced technical workaround: tacking them onto the front of the command. To wit:

```bash
WANDB_API_KEY=your-key-here WANDB_PROJECT=mlops-codecopilot-demo python your-flow.py run --offline False
```

We know this workaround fails to account for scheduling and scripts: we're working on improving this part of the process as soon as possible.

> [!NOTE]  
> We have changed `offline` here to false: hat means we _do_ want our flow to integrate with Weights and Biases!

## Next: Running inference servers in Production

Deploying your Ray Serve app to production requires changes in 3 different repositories: “application repo“, “function specific repo” and “deployment repo“. Please refer to the [glossary](https://mozilla-hub.atlassian.net/wiki/spaces/DATA/pages/785514640/Deploy+inference+servers+to+production+GKE+using+Ray+Serve#Steps-for-deployment) for details on these repositories.

### Steps in “application repo“

> [!NOTE]
> We will use the [template Ray Serve app](./template_ray_serve.py) in this repository to demonstrate the command usage in different steps below. The [original code](https://docs.ray.io/en/latest/serve/develop-and-deploy.html#convert-a-model-into-a-ray-serve-application) for this app comes from the Ray Serve documentation.

#### Test your Ray Serve app locally
Before you run an inference server in production, please make sure that your Ray Serve app runs locally without any issue. The steps to test the template Ray Serve app are as follows:

1. Install requirements

    ```sh
    pip install -r requirements-rayserve.txt
    ```
2. Run Ray Serve app locally using [serve run](https://docs.ray.io/en/latest/serve/api/index.html#serve-run) command

    ```sh
    serve run template_ray_serve:translator_app --route-prefix "/translate"
    ```
3. Check if the locally running service endpoint returns the expected response
    ```sh
    curl -i -d '{"text": "Hello world!"}' -X POST "http://127.0.0.1:8000/translate/" -H "Content-Type: application/json"
    ```

#### Containerize your Ray Serve app

Creating Docker images is the [recommended way]((https://mozilla-hub.atlassian.net/wiki/spaces/DATA/pages/785514640/Deploy+inference+servers+to+production+GKE+using+Ray+Serve#Containerization-of-Ray-Serve-application)) to deploy Ray Serve apps to production.

1. Create a [Dockerfile](https://docs.docker.com/reference/dockerfile/) for your Ray Serve app and add it to the "application repo"

    The Dockerfile for the template Ray Serve app is [here](./Dockerfile-rayserve).

2. [_Optional but highly recommended_] Test if the containerized Ray Serve app works locally
    1. Build the docker image locally using [docker build](https://docs.docker.com/reference/cli/docker/buildx/build/) command:
    ```sh
    docker build -t template_rayserve_image:v1 -f Dockerfile-rayserve .
    ```
    2. Run a container from the image using [docker run](https://docs.docker.com/reference/cli/docker/container/run/) command and start the Ray Serve app locally by running the [serve run](https://docs.ray.io/en/latest/serve/api/index.html#serve-run) command inside the container
    ```sh
    docker run -p 127.0.0.1:8000:8000 -p 127.0.0.1:8265:8265 --name template_rayserve_container --rm template_rayserve_image:v1 serve run -h 0.0.0.0 -p 8000 template_ray_serve:translator_app --route-prefix "/translate"
    ```
    3. Call the service endpoint and check if it returns the expected response for your Ray Serve app
    ```sh
    curl -i -d '{"text": "Hello world!"}' -X POST "http://127.0.0.1:8000/translate/" -H "Content-Type: application/json"
    ```

#### Create a Serve config for your Ray Serve app
The [Serve config](https://docs.ray.io/en/latest/serve/production-guide/config.html#serve-config-files) is the [recommended way](https://docs.ray.io/en/latest/serve/configure-serve-deployment.html#specify-parameters-through-the-serve-config-file) to deploy and update Ray Serve apps in production.

1. Auto-generate the Serve config file using [serve build](https://docs.ray.io/en/latest/serve/api/index.html#serve-build) command
    ```sh
    serve build template_ray_serve:translator_app -o serve_config.yaml
    ```
2. Tweak the auto-generated Serve config file (if needed) as per your Ray Serve app structure
    Details on a Serve config file here. Please make sure the following:
    1. `applications.runtime_env`: This should either be empty or this entry shouldn't exist
    2. `applications.import_path`: Should be correctly set based on the location of your Ray Serve app code inside the container (see Containerize step above)
    3. `applications.route_prefix`: Should be unique for your Ray Serve app on a Ray Cluster. It defaults to `/` and could be left as it is unless you are deploying multiple apps on a single Ray Cluster which is not recommended.

3. Add this Serve config file to your “application repo”

The Serve config file for the template Ray Serve app is [here](./serve_config.yaml).

### Steps in “function specific repo” and “deployment repo“
Please refer to [this guide]() regarding details on the steps in these 2 repos.
