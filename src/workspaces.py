#!/usr/bin/env python3
from dataclasses import dataclass
from pathlib import Path

import argparse
import json
import sys

from thefuzz import fuzz

SEARCH_CONFIDENCE_MIN = 50


@dataclass
class AlfredSuggestion:
    """Class for keeping track of an Alfred suggestion item."""
    # pylint: disable=too-many-arguments
    title: str
    arg: str
    subtitle: str = ""
    valid: bool = True
    variables: dict = None


class GenericSerializer(json.JSONEncoder):
    def default(self, o):
        return o.__dict__


def get_alfred_suggestions(search_term, search_path: Path):
    suggestions = []

    for workspace in search_path.rglob("*.code-workspace"):
        relative_workspace = workspace.relative_to(search_path)
        relative_workspace_string = str(relative_workspace.with_suffix(''))
        search_confidence = fuzz.partial_ratio(
            relative_workspace_string, search_term)

        if search_confidence >= SEARCH_CONFIDENCE_MIN:
            suggestions.append(
                AlfredSuggestion(
                    title=str(workspace.stem),
                    subtitle=relative_workspace_string,
                    arg=str(workspace),
                    variables={
                        'confidence': search_confidence
                    }
                )
            )

    suggestions.sort(key=lambda x: x.variables['confidence'], reverse=True)

    if len(suggestions) == 0:
        suggestions = [
            AlfredSuggestion(
                title=f'No results found for "{search_term}"',
                arg=None
            )
        ]

    response = json.dumps(
        {
            "items": suggestions
        },
        cls=GenericSerializer
    )

    return response


def main():
    parser = argparse.ArgumentParser(
        description="Recursively find VSCode workspace files.")
    parser.add_argument(
        "--folder",
        help="Where to search for files.",
        required=True
    )
    parser.add_argument(
        "--query",
        help="The needle to search for.",
        required=True
    )
    args = parser.parse_args()

    search_folder = Path(args.folder)
    search_term = args.query

    if not search_folder.exists():
        sys.exit(f'Folder "{search_folder}" does not exist')

    print(get_alfred_suggestions(search_term, search_folder))


if __name__ == '__main__':
    main()
