# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring

import os
from dotenv import load_dotenv

load_dotenv()
show_errors_in_console = os.getenv("DEBUG")


def print_logs(text):
    if show_errors_in_console:
        print(text)
