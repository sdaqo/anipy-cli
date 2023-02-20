#!/bin/bash


# Publishing script for GitHub Actions

python -m build
if twine upload dist/* -u __token__ -p $PYPI_API_TOKEN
then 
        rm -rf build dist *.egg-info
fi
