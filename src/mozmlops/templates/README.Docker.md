### Building and running your application

When you're ready, build your image by running:
`docker build`.

Your application will be available at http://localhost:8000.

### Deploying your application to the cloud

First, build your image, e.g.: `docker build -t myapp .`.
If your cloud uses a different CPU architecture than your development
machine (e.g., you are on a Mac M1 and your cloud provider is amd64),
you'll want to build the image for that platform, e.g.:
`docker build --platform=linux/amd64 -t myapp .`.

Then, push it to your registry, e.g. `docker push myregistry.com/myapp`.

Consult Docker's [getting started](https://docs.docker.com/go/get-started-sharing/)
docs for more detail on building and pushing.

### References
* [Docker's Python guide](https://docs.docker.com/language/python/)

## _(Optional)_ Build and push a new Docker image
The Docker image used in the training flow is derived from a python image
and comes with a few additional dependencies required for training. 

The template flow specifies the docker image with the @kubernetes decorator, 
which needs a URL to get the docker image from.

In order to make an updated image available at a URL, you'll need to push it somewhere. The easiest is [Dockerhub](https://hub.docker.com/). You'll need to create an account. It's free; the process is not unlike signing up for a Github account.

Then, change and update the image as follows:

1. Tweak the [`Dockerfile`](Dockerfile-metaflow) as needed.
2. Build the image: `docker build -t mlops-copilot-demo:<TAG> .` where `<TAG>` is an identifier
used to version the image, for example `v3`.
3. Run `docker images` to find the built image and its id.
4. Tag the image with your DockerHub info: `docker tag <Image ID> <DockerHub user>/mozmlops:<TAG>`
  where `<Image ID>` is the id from step 3, `<DockerHub user>` is
  the Docker username and `<TAG>` is the version tag.
5. Run `docker images` again to check that the new tag shows up.
6. Push to Docker hub using `docker push <DockerHub user>/mlops-copilot-demo:<TAG>`.
7. Update the reference image in the `@kubernetes` decorator in [`template_flow.py`](template_flow.py).