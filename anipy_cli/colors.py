class colors:
    """
    Just a class for colors
    """

    GREEN = "\033[92m"
    ERROR = "\033[93m"
    BLUE = "\u001b[34m"
    YELLOW = "\u001b[33m"
    MAGENTA = "\u001b[35m"
    CYAN = "\u001b[36m"
    RED = "\u001b[31m"
    END = "\x1b[0m"


def color(*values: str, sep: str = "") -> str:
    """Decorate a string with color codes.
    Basically just ensures that the color doesn't "leak"
    from the text.
    format: color(color1, text1, color2, text2...)"""
    return sep.join(values) + colors.END


def cinput(*prompt: str, input_color: str = "") -> None:
    """An input function that handles coloring input."""
    inp = input(color(*prompt) + input_color)
    print(colors.END, end="")
    return inp


def cprint(*values: str, sep: str = "", **kwargs) -> None:
    """Prints colored text."""
    print(color(*values, sep=sep), **kwargs)
