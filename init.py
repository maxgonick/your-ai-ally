from termcolor import colored
import pyfiglet


def init():
    f = pyfiglet.figlet_format("Your AI Ally", font="slant")
    print(colored(f, "light_magenta"))
    print(
        colored(
            "Welcome to your AI Ally! Please input a valid URL of the site to be parsed:",
            "light_cyan",
        )
    )
    url = input("> ")


if __name__ == "__main__":
    init()
