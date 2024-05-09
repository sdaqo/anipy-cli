# Contributing

Hey thanks for considering to contribute! If you did this before you probably know the gist, but check out this little guide to get everything set-up!

## Setup environment for code changes
1. Install [Poetry](https://python-poetry.org/docs/#installation) for project managment, it is like pip but better and feature-richer. You can work on this project without it, but I highly recommend you not do this.
2. Clone: `git clone https://github.com/sdaqo/anipy-cli && cd anipy-cli`
3. Initiate your environment: `poetry install --with dev,docs`

## Formatting 'n stuff

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
No. I am frankly to lazy to write tests, but I do have it on my to-do, but expect nothing!
