from setuptools import find_packages, setup

setup(
    name='anipy_cli',
    packages=find_packages(include=['anipy_cli']),
    version='2.0',
    description='Little tool in python to watch anime from the terminal (the better way to watch anime)',
    author='sdaqo',
    license='GPL-3.0',
    install_requires=['bs4', 'requests', ''],
    entry_points="[console_scripts]\nanipy-cli=anipy_cli.cli:main",
)
