# Training and Deploying Models in The Cloud

So you're a Mozillian with a machine learning model that you have futzed with locally, or maybe in Google Colab, or possibly even on your own cluster. You’re now ready for a more sophisticated model orchestration setup. 

Excellent! You've found the toolset for this. We use deployed Metaflow flows with Outerbounds to do model orchestration, and we use Weights and Biases for experiment evaluation. The templates in this repository will help you integrate with both.

## But first...you need some stuff.

### Most importantly, you need an account with Outerbounds (do not make this yourself).

An admin from Mozilla’s MLOps team needs to make you a user account in our production Outerbounds instance. You can ask for help with this in the #mlops Slack channel.

**The admins need to know two things:**
1. If your data requires more restricted access than All-Mozilla. If so, they will handle getting a perimeter created for you, and will get back to you with your Outerbounds login information and perimeter name. 
1. If you intend to run your flow on your own cluster or your own servers, rather than Outerbounds resources. If yes, they need to set that up. Let them know and they’ll work with you on that.

Once MLOps comes back to you with a shiny new Outerbounds account and a perimeter for your team, you can sign in [here](https://docs.google.com/document/d/12S06Q-9xh6YGkyBpi6iGWGazYDivxl2fT4KaHtbrzV4/edit).

Go to [this page right here](https://ui.desertowl.obp.outerbounds.com/dashboard/configure?location=local). You’ll see some instructions. You have already installed Outerbounds, so you get to skip that one. 
Look for a dropdown that says “perimeter.” You want to make sure that, if your data has more restricted access than All-Mozilla, you have checked the perimeter name that you received from MLOps. If your data has all-Mozilla access, you can check “default” here.

You should see an instruction to run a command line command that starts with `outerbounds configure`. Copy that whole thing and run it on your command line. What this does, is it makes a `config.json` file located at `~/.metaflowconfig` on your local machine. This is the default configuration for metaflow on your machine now, and unless told otherwise, metaflow flows on your machine will now always run on Outerbounds. 

### Running the template Metaflow flow

1. Install the requirements listed in [`templates/requirements.txt`](`templates/requirements.txt`) and also add those to your project requirements files.
2. Copy the `template_flow.py` file from this repo into _your_ repo. From there, you can run `python template_flow.py run --offline True`.

> [!TIP]
>The `--offline True` command line argument tells the template flow to not track experiments on W&B.

The Metaflow flow will run internal consistency checks and linting, and then provide a link to track the progress of the flow on our platform, see stderr and stdout, et cetera. 

Eventually you should see the flow finish with "Task finished successfully." Once you see that, you know you've got a working minimal flow: you're now ready to start putting your model training code _into_ this flow to run it remotely. Comments _inside_ the template file should help you understand where to put that code, and demonstrate some of the tools Metaflow makes available to you.

 ## Next: A Fancy Dashboard

An admin from Mozilla’s MLOps team needs to set you up with a Weights and Biases User account, and also a team if your team doesn’t have that yet, on Weights and Biases. Reach out to #mlops in Slack for help with this.

MLOps needs to know:
1. If you will need a service account for your Weights and Biases team—say, to set up CI or something. Seats cost significant amounts of money, so if you need extra accounts “just in case,” no you don’t. But if you are, for example, already set up with CI for your model and you want that on Weights and Biases, we can get you a service account for that.

Once you have the account, you're in luck; the `template_flow` already integrates with Weights and Biases for you. 

Note the three environment variables listed at the top of the `train` step:

- The `WANDB_API_KEY` you can get by going to [this page](https://wandb.ai/), once your wandb credentials are set up (see the account provisioning section). Treat this with the sensitive that you would treat any API key. You will see in a later step how to use this string; for now, you can stick this in your local repository’s .env. 

- The `WANDB_ENTITY` is your wandb username or the service account username (provided to you by the MLOps upon request). 

- The `WANDB_PROJECT` is the name of the project that this run is for. You can see and create projects for your team at this URL: https://wandb.ai/YOUR_TEAM_NAME_HERE/projects.

You can customize what you send to Weights and Biases as well as the graphs and data that appears there, and the team maintains decent documentation on your customization options. The wandb engineering support team is also incredibly helpful. Talk to MLOps about your problem and they can get you added to our joint channel with wandb where folks are available to help.


When it’s time to run your flow on outerbounds with your weights and biases dashboard set up, the Outerbounds instance will not have the three environment variables we just talked about. We are currently working on that with them for things like scheduled flows. In the meantime, when you kick off the flow from your local machine, you can specify the environment variables via our super-advanced technical workaround: tacking them onto the front of the command. To wit:

```bash
WANDB_API_KEY=your-key-here WANDB_ENTITY=ctroy WANDB_PROJECT=mlops-codecopilot-demo python your-flow.py run --offline False
```
> [!NOTE]  
> We have changed `offline` here to false: hat means we _do_ want our flow to integrate with Weights and Biases!

