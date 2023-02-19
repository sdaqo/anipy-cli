from setuptools import find_packages, setup


def read_version():
    fname = "anipy_cli/version.py"
    with open(fname) as fh:
        version_file = fh.read()

    exec(compile(version_file, fname, "exec"))
    return locals()["__version__"]


with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="anipy_cli",
    packages=find_packages(include=["anipy_cli", "anipy_cli.*"]),
    version=read_version(),
    python_requires=">3.9",
    description="Little tool in python to watch anime from the terminal (the better way to watch anime)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="sdaqo",
    author_email="sdaqo.dev@protonmail.com",
    url="https://github.com/sdaqo/anipy-cli",
    license="GPL-3.0",
    install_requires=[
        "better-ffmpeg-progress",
        "pycryptodomex",
        "requests",
        "python-dateutil",
        "pypresence",
        "m3u8",
        "setuptools",
        "beautifulsoup4",
        "tqdm",
        "moviepy",
        "pyyaml",
        "python-mpv",
    ],
    entry_points="[console_scripts]\nanipy-cli=anipy_cli.run_anipy_cli:main",
)
