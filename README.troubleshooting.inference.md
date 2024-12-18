
## If you see a redis cleanup pod hanging there in the cluster for your deployment... 

it means some redis error has happened during killing your pod. 

In this case, run the following commands (You'll need k8s cluster access to run them - [here's how to get that](https://mozilla-hub.atlassian.net/wiki/spaces/DATA/pages/785514640/Deploy+inference+servers+to+production+GKE+using+Ray+Serve#Running-kubectl/helm-commands)):

    kubectl get raycluster -n <xxx> to get the raycluster name for your deployment.

    kubectl edit rayclusters.ray.io -n <xxx> <ray_cluster_name> to bring up the yaml for the deployment.

    Find finalizers: - ray.io/gcs-ft-redis-cleanup-finalizer and delete those 2 lines and save.

    This should apply the change and allow kuberay to clean up the ray cluster without needing the redis cleanup thing to run.

Likely this can be due to your pod name being too long, which translates to your application name being too long. SHORTEN your application name.

## Test Deployment Changes From Local

In order to avoid too many subsequent PRs to dataservices or webservices repo, it’s better to test deployment changes from local when you are done so that you can debug without the hassle of going through all the PR review and approval steps.

To apply changes in your helm charts to the target environment, you do the following in your project folder (i.e. fakespot-ml/k8s/<app_name>):

```
helm upgrade \
    <app_name> . \
    -f values-prod.yaml \
    --set image.tag=latest \
    -f <local_path_to_your_api_repo>/configs/config_staging.yaml \
    --set ghaRunId=<URL_for_your_last_deployment_run> \
    --set rayImageTag=<latest_tag> \
    -n fakespot-ml-{prod|stage}
```

Notable notes:

    ghaRunId is the link to your last deployment run in your deployment repo.

    rayImageTag is the tag of the API repo to use for deployment. You can get this from the ghaRun above and check the determine tag section of the build log.

    You will need gcp-bastion-tunnel running in the backend when running the command.

For example, the command below will apply changes to fakespot-dfd-open-source in prod cluster:

```
helm upgrade \
    fakespot-dfd-open-source . \
    -f values-prod.yaml \
    --set image.tag=latest \
    -f ~/Documents/Projects/AIContentDetection/FakespotDFDOpenSourceAPI/configs/config_production.yaml \
    --set ghaRunId=https://github.com/mozilla-sre-deploy/deploy-fakespot-dfd-open-source/actions/runs/11298260133 \
    --set rayImageTag=v1.2 \
    -n fakespot-ml-prod
```

Create the PR after everything seems to be working.