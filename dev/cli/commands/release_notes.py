# ruff: noqa: S603
# ruff: noqa: S607
# ruff: noqa: E402 Django must be configured before its settings can be imported.

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import django

from dev import cms_package_dir
from dev.cli.deepl import deepl_translate
from dev.utils import (
    print_bold,
    print_error,
    print_info,
    print_success,
    print_warning,
)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "integreat_cms.core.settings")
django.setup()

from django.conf import settings

_release_notes_dir = cms_package_dir / "release_notes"


def new(
    issue: int,
    language: str,
    text: str | None,
    overwrite: bool,
) -> None:
    if not text or text.startswith("-"):
        print_error(
            "The third command line argument needs to contain the release note text."
        )
        sys.exit(1)

    if language == "en":
        source_lang, target_lang = "EN", "DE"
    else:
        source_lang, target_lang = "DE", "EN"

    unreleased_dir = cms_package_dir / "release_notes" / "current" / "unreleased"
    file_path = unreleased_dir / f"{issue}.yml"

    # Retrieve the issue title from GitHub
    print_info(f"➡ Retrieve issue title for issue #{issue} from github")
    title = json.loads(
        subprocess.run(
            ["gh", "issue", "view", str(issue), "--json", "title"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    )["title"]

    print_info(f"➡ Creating new release note for issue #{issue} with title:")
    print_bold(f"  {title}")

    # Retrieve the DeepL auth key from the Django settings
    _deepl_auth_key = settings.DEEPL_AUTH_KEY or ""

    if _deepl_auth_key:
        _text_translated = deepl_translate(
            auth_key=_deepl_auth_key,
            source_lang=source_lang,
            target_lang=target_lang,
            text=text,
        )
    else:
        print_warning(
            "➡ Set a DeepL auth key in the config file to enable automatic translation of release notes."
        )
        _text_translated = ""

    if language == "en":
        text_en, text_de = text, _text_translated
    else:
        text_en, text_de = _text_translated, text

    if file_path.is_file():
        print_warning(f"➡ Warning: The release note {file_path} already exists.")

        if overwrite:
            print_warning("  The existing file will be overwritten.")
        else:
            print_warning("  Use the --overwrite flag to overwrite the existing file.")
            sys.exit(1)

    content = f"en: {text_en}\nde: {text_de}\n"
    unreleased_dir.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")

    print_success(f"✔ The new release note has been generated: {file_path}\n")
    print_info(content)


def make(
    all: bool,
    format: str,
    language: str,
    output: str | None,
    no_heading: bool,
    no_subheading: bool,
    version: str,
) -> None:
    def _version_key(name: str) -> list[tuple[int, int, str]]:
        """Emulate GNU ``sort --version-sort`` well enough for release note paths."""
        return [
            (0, int(token), "") if token.isdigit() else (1, 0, token)
            for token in re.split(r"(\d+)", name)
        ]

    def _extract_text(yml_file: Path) -> str:
        pattern = re.compile(rf"{language}: (.*)")
        for line in yml_file.read_text(encoding="utf-8").splitlines():
            if match := pattern.search(line):
                return match.group(1)
        return ""

    def _format_entry(yml_file: Path) -> str:
        issue = yml_file.stem
        text = _extract_text(yml_file)
        match format:
            case "md":
                return (
                    f"- [ [#{issue}](https://github.com/digitalfabrik/integreat-cms/issues/"
                    f"{issue}) ] {text}"
                )
            case "rst":
                return f"* [ :github-issue:`{issue}` ] {text}"
            case _:
                return f"- [ #{issue} ] {text}"

    def _format_version(version_dir: Path) -> str:
        parts: list[str] = []
        if not no_subheading:
            version = version_dir.name
            if format == "raw":
                parts.append(f"{version}\n\n")
            elif format == "md":
                parts.append(f"## {version}\n\n")
            elif version == "unreleased":
                parts.append(f"{version}\n{'-' * len(version)}\n\n")
            else:
                heading = f":github:`{version} <releases/tag/{version}>`"
                parts.append(f"{heading}\n{'-' * len(heading)}\n\n")
        parts.extend(
            f"{_format_entry(yml_file)}\n"
            for yml_file in sorted(
                version_dir.glob("*.yml"), key=lambda p: _version_key(p.name)
            )
        )
        parts.append("\n\n")
        return "".join(parts)

    def _strip_trailing_blank_lines(text: str) -> str:
        """Emulate the ``sed '$ d' | sed '$ d'`` that trims the two trailing blank lines."""
        lines = text.split("\n")[:-1][:-2]
        return "".join(f"{line}\n" for line in lines)

    version_text = (
        ""
        if all
        else (f"for version {version}" if version else " for the latest version")
    )

    if output is None:
        print_info(f"Building release notes {version_text}...")

    output_parts: list[str] = []

    if not no_heading:
        match format:
            case "md":
                output_parts.append("# Release notes\n\n")
            case "rst":
                output_parts.append(f"Release notes\n{'=' * len('Release notes')}\n\n")
            case _:
                output_parts.append("Release notes\n\n")

    if version:
        version_path = "current" if version == "unreleased" else version[:4]
        version_dir = _release_notes_dir / version_path / version

        if version_dir.is_dir():
            output_parts.append(
                _strip_trailing_blank_lines(_format_version(version_dir))
            )
        else:
            print_error(f"The given version '{version}' does not exist.")
            sys.exit(1)
    elif all:
        years = sorted(
            (d for d in _release_notes_dir.iterdir() if d.is_dir()),
            key=lambda p: p.name,
            reverse=True,
        )
        for year in years:
            output_parts.extend(
                _format_version(version)
                for version in sorted(
                    (d for d in year.iterdir() if d.is_dir()),
                    key=lambda p: _version_key(p.name),
                    reverse=True,
                )
            )
    else:
        note_dirs = [
            version
            for year in _release_notes_dir.iterdir()
            if year.is_dir()
            for version in year.iterdir()
            if version.is_dir()
        ]
        unreleased_dir = _release_notes_dir / "current" / "unreleased"

        # If there are no release notes in unreleased, pretend it's not there
        if not any(unreleased_dir.glob("*.yml")):
            note_dirs = [d for d in note_dirs if d != unreleased_dir]

        if note_dirs:
            # Only return the latest version by default
            latest_version_dir = max(note_dirs, key=lambda p: _version_key(str(p)))
            output_parts.append(
                _strip_trailing_blank_lines(_format_version(latest_version_dir))
            )
        else:
            print_error("No release notes found")
            sys.exit(1)

    content = "".join(output_parts)

    if output is None:
        sys.stdout.write(content)
    else:
        Path(output).write_text(content, encoding="utf-8")
        print_success("✔ The release notes have been generated:\n")
        print_bold(f"{content}\n")
