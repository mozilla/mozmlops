# mozmlops

A package for getting your models into production!

## Installation

For now, we're not distributing to a package index. But you can install locally! We use a local build manager called poetry for this.

Steps:

1. Clone this repository
2. `cd` into the repository
3. Start up a virtual environment:
```
python -m venv env
source env/bin/activate
```
3. `python -m pip install poetry`
4. `poetry install mozmlops`

## Usage

An example import line (in fact, the only one currently implemented) would be:

```
from mozmlops.artifact_store import ArtifactStore
```

at the top of your favorite Python file, or in a python console. From there, you can try running this line:

```
store = ArtifactStore('some-project-name', 'some-bucket-name')
```

To make sure the import worked.

## Contributing

Interested in contributing? Check out the contributing guidelines. Please note that this project is released with a Code of Conduct. By contributing to this project, you agree to abide by its terms.

## License

`mozmlops` was created by Mozilla MLOps. It is licensed under the terms of the Mozilla Public License.

## Credits

`mozmlops` was created with [`cookiecutter`](https://cookiecutter.readthedocs.io/en/latest/) and the `py-pkgs-cookiecutter` [template](https://github.com/py-pkgs/py-pkgs-cookiecutter).
