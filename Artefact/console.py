"""Small interactive front end for the ArteFact CLI."""

import shlex
from typing import Callable


def interactive_mode(input_fn: Callable[[str], str] = input) -> int:
    """Run commands until the user chooses to exit."""
    from Artefact.cli import TOOLS, main

    print("ARTEFACT interactive mode. Type 'help' or 'quit'.")
    while True:
        try:
            command = input_fn("artefact> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if not command:
            continue
        if command.lower() in {"quit", "exit", "q"}:
            return 0
        if command.lower() == "help":
            for name, description in TOOLS.items():
                print(f"  {name:<10} {description}")
            continue
        main(shlex.split(command, posix=False))
