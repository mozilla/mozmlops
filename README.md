# mozmlops

A package for getting your models into production!

## For the Model Orchestration/Experiment Evaluation Flow Template

You'll find a README in the [src/mozmlops/templates directory](https://github.com/mozilla/mozmlops/tree/main/src/mozmlops/templates)!

## Installation for use

You can install the library with `pip install mozmlops`.

## Installation for local testing and contributing

Steps:

1. Clone this repository
2. `cd` into the repository
3. Start up a virtual environment:
```
python -m venv env
source env/bin/activate
```
3. `python -m pip install poetry`
4. `poetry install`

## Running tests

**Linting:**

Run `ruff check` to find style issues and `ruff check --fix` to fix many automatically.

**Unit tests:**

Run `pytest` from the top-level directory.

**Integration tests:**

You need to be logged into GCP to run the integration tests; you can use the gcloud CLI command `gcloud auth login`. 

Run the integration tests with `pytest -m integration`.

## Usage

An example import line (in fact, the only one currently implemented) would be:

```
from mozmlops.storage_client import CloudStorageAPIClient
```

at the top of your favorite Python file, or in a python console. 

From there, you can try running this line:

```
store = CloudStorageAPIClient('some-project-name', 'some-bucket-name')
```

To make sure the import worked.

## Contributing

Interested in contributing? Check out the contributing guidelines. Please note that this project is released with a Code of Conduct. By contributing to this project, you agree to abide by its terms.

## License

`mozmlops` was created by Mozilla MLOps. It is licensed under the terms of the Mozilla Public License.

## Credits

`mozmlops` was created with [`cookiecutter`](https://cookiecutter.readthedocs.io/en/latest/) and the `py-pkgs-cookiecutter` [template](https://github.com/py-pkgs/py-pkgs-cookiecutter).
