# Installing OPTiMaDe Python tools

## The index meta-database

This package may be used to setup and run an [OPTiMaDe index meta-database](https://github.com/Materials-Consortia/OPTiMaDe/blob/develop/optimade.rst#index-meta-database).
Install the package via `pip install optimade[server]` and change the file [`server.cfg`](server.cfg) found in the root of the package.

The `server.cfg` file serves paths to a server runtime configuration file (either an `ini` or `json` file, see the [`config.ini` file](optimade/server/config.ini) for an example) and an index `/links`-endpoint data file.
The paths must be relative from your current working directory, where your `server.cfg` is located, or they must be absolute paths.

The index meta-database is set up to populate a `mongomock` in-memory database with resources from a static `json` file containing the `child` resources you, as a database provider, want to serve under this index meta-database.

Running the index meta-database is then as simple as writing `./run.sh index` in a terminal from the root of this package.
You can find it at the base URL: <http://localhost:5001/v0.10.1>.

_Note_: `server.cfg` is loaded from the current working directory, from where you run `run.sh`.
E.g., if you have installed `optimade` on a Linux machine at `/home/USERNAME/optimade/optimade-python-tools` and you run the following:

```shell
:~$ ./optimade/optimade-python-tools/run.sh index
```

Then you need `server.cfg` to be located in your home folder containing either relative paths from its current location or absolute paths.

## Full development installation

The dependencies of this package can be found in `setup.py` with their latest supported versions.
By default, a minimal set of requirements are installed to work with the filter language and the `pydantic` models.
The install mode `server` (i.e. `pip install .[server]`) is sufficient to run a `uvicorn` server using the `mongomock` backend (or MongoDB with `pymongo`, if present).
The suite of development and testing tools are installed with via the install modes `dev` and `testing`.
There are additionally three backend-specific install modes, `django`, `elastic` and `mongo`, as well as the `all` mode, which installs all dependencies.
All contributed Python code, must use the [black](https://github.com/ambv/black) code formatter, and must pass the [flake8](http://flake8.pycqa.org/en/latest/) linter that is run automatically on all PRs.

```shell
# Clone this repository to your computer
git clone git@github.com:Materials-Consortia/optimade-python-tools.git
cd optimade-python-tools

# Ensure a Python>=3.7 (virtual) environment (example below using Anaconda/Miniconda)
conda create -n optimade python=3.7
conda activate optimade

# Install package and dependencies in editable mode (including "dev" requirements).
pip install -e .[dev]

# Run the tests with pytest
py.test

# Install pre-commit environment (e.g., auto-formats code on `git commit`)
pre-commit install

# Optional: Install MongoDB (and set `USE_REAL_MONGO = yes` in optimade/server/congig.ini)
# Below method installs in conda environment and
# - starts server in background
# - ensures and uses ~/dbdata directory to store data
conda install -c anaconda mongodb
mkdir -p ~/dbdata && mongod --dbpath ~/dbdata --syslog --fork

# Start a development server (auto-reload on file changes at http://localhost:5000
# You can also execute ./run.sh
uvicorn optimade.server.main:app --reload --port 5000

# View auto-generated docs
open http://localhost:5000/docs
# View Open API Schema
open http://localhost:5000/openapi.json
```

When developing, you can run both the server and an index meta-database server at the same time (from two separate terminals).
Running the following:

```shell
./run.sh index
# or
uvicorn optimade.server.main_index:app --reload --port 5001
```

will run the index meta-database server at <http://localhost:5001/v0.10.1>.