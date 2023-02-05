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

def color(*colors_texts) -> str:
    """Decorate a string with color codes.
    format: color(color1, text1, color2, text2...)"""
    if colors_texts and len(colors_texts) % 2 == 0:
        return "".join(colors_texts) + colors.END
    return ''