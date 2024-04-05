#!/bin/python
from anipy_cli.cli import cli
from anipy_cli.misc import keyboard_inter
import sys

def main():
    # try:
    cli.run_cli()
    # except Exception as e:
    #     print(f"anipy-cli fatal error: {str(e)}")


if __name__ == "__main__":
    main()
