# Training and Deploying Models in The Cloud

So you're a Mozillian with a machine learning model that needs production-grade infrastructure. Excellent! You've found the toolset for this. 

We use deployed Metaflow flows with Outerbounds to do model orchestration, and we use Weights and Biases for experiment evaluation. 

The templates in this repository will help you integrate with both.

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

