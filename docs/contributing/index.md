# Contributing

Hey, thanks for considering to contribute!

If you did this before you probably know the gist, but check out this little guide to get everything set-up!

## Setup environment for code/docs changes
1. Install [Poetry](https://python-poetry.org/docs/#installation) for project managment, it is like pip but better and feature-richer. You can work on this project without it, but I highly recommend not to do this.
2. Clone: `git clone https://github.com/sdaqo/anipy-cli && cd anipy-cli`
3. Initiate your environment: `poetry install --with dev,docs`, this installs all the dependencies and some development tools.
4. Open your edior, you can either run `poetry run <your-editor>` or `poetry shell` to get a shell in the virtual environment and run your editor from there, some editors like vscode automatically enter the venv as far as I know.
4. Make your changes :)
5. Check your changes
    - Run `poetry run anipy-cli` to run the cli.
    - Run `poetry run python` to run python from the virtual environment.
    - Run `poetry run poe docs-serve` to open host the docs locally, this is helpful if you are making changes to the docs.
6. Run `poetry run poe polish` before commiting to format and lint your code. The linter will tell you what you did wrong, fix that if you think the suggestion from the linter is reasonable, if not don't bother. Also, please do not concern yourself with linter errors that you did not introduce!
7. Push & Pull Request!

## Project structure
```
.
├── api
│   ├── pyproject.toml # spec file for api
│   └── src 
│       └── anipy_api # api source
├── cli
│   ├── pyproject.toml # spec file for cli
│   └── src 
│       └── anipy_cli # cli source
├── docs # documentation
│   └── ...
├── mkdocs.yml # documentation config
├── pyproject.toml # (spec) file for whole project
└── scripts # utility scripts
    └── ...
```

## Tests
No. Frankly, I am to lazy to write tests, but I do have it on my to-do, expect nothing though!
