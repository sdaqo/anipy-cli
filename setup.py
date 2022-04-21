from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="anipy_cli",
    packages=find_packages(include=["anipy_cli"]),
    version="2.4.8",
    python_requires=">3.9",
    description="Little tool in python to watch anime from the terminal (the better way to watch anime)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="sdaqo",
    author_email="sdaqo.dev@protonmail.com",
    url="https://github.com/sdaqo/anipy-cli",
    license="GPL-3.0",
    install_requires=[
        "bs4",
        "requests",
        "tqdm",
        "pycryptodomex",
        "better-ffmpeg-progress",
        "kitsu.py-extended",
        "pypresence",
        "python-dateutil",
        "m3u8",
        "tqdm",
        "moviepy",
    ],
    entry_points="[console_scripts]\nanipy-cli=anipy_cli.run_anipy_cli:main",
)
