# ruff: noqa: S603
# ruff: noqa: S607

import re
import sys
from subprocess import run

from dev import cms_admin_cli, cms_package_dir, project_home
from dev.utils import print_bold, print_error, print_info

_translation_file = cms_package_dir / "locale" / "de" / "LC_MESSAGES" / "django.po"
_date_regex = re.compile(
    r'^"POT-Creation-Date: [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}\+[0-9]{4}\\n"$',
    re.UNICODE | re.MULTILINE,
)
_date_replacement = r'"POT-Creation-Date: YEAR-MO-DA HO:MI+ZONE\\n"'


def _print_context(
    lines: list[str], indices: list[int], before: int, after: int
) -> None:
    shown: set[int] = set()
    for index in indices:
        for line_number in range(
            max(0, index - before), min(len(lines), index + after + 1)
        ):
            if line_number not in shown:
                print_bold(f"{line_number + 1}: {lines[line_number]}")
                shown.add(line_number)


def check() -> None:
    print_info("➡ Checking translation files for problems...")
    # Re-generate the translation file (without compiling)
    run(
        [
            cms_admin_cli,
            "makemessages",
            "-l",
            "de",
            "--add-location",
            "file",
        ],
        check=True,
        cwd=cms_package_dir,
    )

    # Reset POT-Creation-Date to avoid spurious diffs
    with open(_translation_file, mode="r+", encoding="utf-8") as file:
        content = file.read()
        updated_content = _date_regex.sub(_date_replacement, content, count=1)
        if content != updated_content:
            file.seek(0)
            file.write(updated_content)
            file.truncate()
            content = updated_content

    lines = content.split("\n")

    # Check whether the regenerated file differs from the committed version
    translation_diff = run(
        ["git", "diff", "--shortstat", "--", str(_translation_file)],
        cwd=project_home,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    # Check for empty entries (an empty msgstr followed by a blank line)
    empty_entries = [
        index
        for index, line in enumerate(lines)
        if line == 'msgstr ""' and index + 1 < len(lines) and lines[index + 1] == ""
    ]

    # Check for fuzzy headers (automatic translation proposals)
    fuzzy_entries = [index for index, line in enumerate(lines) if "#, fuzzy" in line]

    if translation_diff or empty_entries or fuzzy_entries:
        if translation_diff:
            print_error("❌ Your translation file is not up to date! 💣")
            print_error(
                "Please re-generate the translations and add the changes to your commit:\n"
            )
            run(
                ["git", "--no-pager", "diff", "--color", "--", str(_translation_file)],
                check=True,
                cwd=project_home,
            )
        if empty_entries:
            print_error(
                "❌ You have empty entries in your translation file. Please translate them manually:\n"
            )
            print_bold(str(_translation_file))
            _print_context(lines, empty_entries, before=2, after=0)
        if fuzzy_entries:
            print_error(
                "❌ You have fuzzy headers in your translation file (See [1] for more information)."
            )
            print_error(
                "Please review them manually, adjust the translation if necessary and remove the fuzzy header afterwards.\n"
            )
            print_bold(str(_translation_file))
            _print_context(lines, fuzzy_entries, before=1, after=3)
            print_error(
                "[1]: https://www.gnu.org/software/gettext/manual/html_node/Fuzzy-Entries.html\n"
            )
        sys.exit(1)

    print_info("✔ Your translation file looks good!")


def compile() -> None:
    print_info("➡ Extracting translation strings")
    run(
        [
            cms_admin_cli,
            "makemessages",
            "-l",
            "de",
            "--add-location",
            "file",
            # "--verbosity",
        ],
        check=True,
        cwd=cms_package_dir,
    )

    # Reset POT-Creation-Date to avoid git conflicts
    with open(_translation_file, mode="r+", encoding="utf-8") as file:
        content = file.read()
        updated_content = _date_regex.sub(_date_replacement, content, count=1)

        if content != updated_content:
            file.seek(0)
            file.write(updated_content)

    #
    # Skip compilation if --skip-compile option is given
    # if [[ "$*" != *"--skip-compile"* ]]; then
    # Compile translation file
    print_info("➡ Compiling translation file")
    run(
        [
            cms_admin_cli,
            "compilemessages",
            # "--verbosity" "${SCRIPT_VERBOSITY}"
        ],
        check=True,
        cwd=cms_package_dir,
    )
