from setuptools import setup, find_packages

VERSION = '0.0.1'
DESCRIPTION = 'Artifact store tools'
LONG_DESCRIPTION = 'Tools for interacting with GCS in our model flows'

# Setting up
setup(
    name="artifactstore",
    version=VERSION,
    author="Mozilla",
    author_email="<ctroy@mozilla.com>",
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    packages=find_packages(),
    install_requires=[],  # add any additional packages that
    # needs to be installed along with your package. Eg: 'caer'

    keywords=['python', 'machine learning operations', 'mozilla'],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
    ]
)