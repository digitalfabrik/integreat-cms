# ruff: noqa: S603
# ruff: noqa: S607
# ruff: noqa: T201

import re
import subprocess
import sys
from os import environ
from pathlib import Path
from shutil import copy, copytree, rmtree
from subprocess import run

import sphinx_rtd_theme

from dev import cms_package_dir, is_running_in_ci, project_home
from dev.utils import print_bold, print_error, print_info

_docs_dir = project_home / "docs"
_docs_dist_dir = _docs_dir / "dist"
_docs_src_dir = _docs_dir / "src"
_apidoc_src_dir = _docs_src_dir / "ref"
_apidoc_ext_src_dir = _docs_src_dir / "ref-ext"
_patches_dir = _docs_src_dir / "patches"
_templates_dir = _docs_src_dir / "templates"
_theme_dir = Path(sphinx_rtd_theme.__file__).parent
_keywords = (
    ("Cms", "CMS"),
    ("Api", "API"),
    ("Poi", "POI"),
    ("Mfa", "MFA"),
    ("Pdf", "PDF"),
    ("Xliff1", "XLIFF 1.2"),
    ("Xliff2", "XLIFF 2.0"),
    ("Xliff", "XLIFF"),
)


def _suggest_clean_parameter() -> None:
    print_info(
        "\nIf you think the above error is not your fault, try a clean documentation build with:\n"
    )
    print_bold("\tpython -m tools.local.release_notes --clean\n")


def _capture(args: list[str | Path]) -> subprocess.CompletedProcess[str]:
    return run(
        [str(arg) for arg in args],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
    )


def _apply_keywords(line: str) -> str:
    for search, replace in _keywords:
        line = line.replace(search, replace)
    return line


def _patch_ext_rst(path: Path) -> None:
    lines = path.read_text(encoding="utf-8").split("\n")
    result: list[str] = []
    skip_next = False

    for line in lines:
        if skip_next:
            skip_next = False
            continue
        # Remove Sub-Headings including their following (underline) line
        if "Submodules" in line or "Subpackages" in line:
            skip_next = True
            continue
        # Remove module & package strings at the end of headings
        heading = re.sub(r" module| package", "", line, count=1)
        if heading and " " not in heading:
            # Remove module path in headings and make first letter uppercase
            heading = re.sub(
                r"(?:.*\.)?([^.]+)",
                lambda match: match.group(1)[:1].upper() + match.group(1)[1:],
                heading,
                count=1,
            )
            # Replace \_ with spaces and make the following letter uppercase
            heading = re.sub(
                r"\\_([a-z])", lambda match: " " + match.group(1).upper(), heading
            )
        result.append(_apply_keywords(heading))
    path.write_text("\n".join(result), encoding="utf-8")


def _patch_ref_rst(path: Path) -> None:
    result: list[str] = []
    for line in path.read_text(encoding="utf-8").split("\n"):
        # Remove undoc-members and inherited-members from the normal reference
        if ":undoc-members:" in line or ":inherited-members:" in line:
            continue
        result.append(line)
        # Insert :noindex: after the :show-inheritance: option
        if ":show-inheritance:" in line:
            result.append("   :noindex:")
    path.write_text("\n".join(result), encoding="utf-8")


def docs(clean: bool) -> None:
    # Remove stale doc files
    if clean:
        print_info("➡ Removing temporary documentation files")
        for stale_dir in (_docs_dist_dir, _apidoc_src_dir, _apidoc_ext_src_dir):
            rmtree(stale_dir, ignore_errors=True)

    # sys.exit(0)
    # elif is_running_in_ci():
    #     # Suggest the --clean parameter when a non-clean, non-CircleCI build fails
    #     _suggest_clean = True

    print_info("➡ Patching Sphinx templates")

    # Copy and patch the footer template to add hyperlinks to copyright information
    copy(_theme_dir / "footer.html", _templates_dir)
    if (
        run(
            ["patch", _templates_dir / "footer.html", _patches_dir / "footer.diff"],
            check=False,
            stdin=subprocess.DEVNULL,
        ).returncode
        != 0
    ):
        print_error(
            "\nThe patch for the footer template could not be applied correctly.\n"
            "Presumably the upstream repository of sphinx_rtd_theme changed.\n"
            f"Please adapt {_patches_dir / 'footer.diff'} to the upstream changes."
        )
        sys.exit(1)

    # Copy and patch the breadcrumbs template
    copy(_theme_dir / "breadcrumbs.html", _templates_dir)
    if (
        run(
            [
                "patch",
                _templates_dir / "breadcrumbs.html",
                _patches_dir / "breadcrumbs.diff",
            ],
            check=False,
            stdin=subprocess.DEVNULL,
        ).returncode
        != 0
    ):
        print_error(
            "\nThe patch for the breadcrumbs template could not be applied correctly.\n"
            "Presumably the upstream repository of sphinx_rtd_theme changed.\n"
            f"Please adapt {_patches_dir / 'breadcrumbs.diff'} to the upstream changes."
        )
        sys.exit(1)

    print_info(
        "➡ Scanning Python source code and generating reStructuredText files from it"
    )

    _sphinx_env = {
        **environ,
        "SPHINX_APIDOC_OPTIONS": "members,undoc-members,inherited-members,show-inheritance",
    }

    # Generate new .rst files from source code for maximum verbosity
    run(
        [
            "sphinx-apidoc",
            "--no-toc",
            "--module-first",
            "-o",
            _apidoc_ext_src_dir,
            cms_package_dir,
            cms_package_dir / "cms" / "migrations",
        ],
        check=True,
        env=_sphinx_env,
    )

    # Generate rst files for tests module
    run(
        [
            "uv",
            "run",
            "sphinx-apidoc",
            "--no-toc",
            "--module-first",
            "-o",
            _apidoc_ext_src_dir,
            project_home / "tests",
        ],
        check=True,
        env=_sphinx_env,
    )

    print_info("➡ Patching reStructuredText files")

    # Modify .rst files to remove unnecessary submodule- & subpackage-titles
    for rst_file in _apidoc_ext_src_dir.rglob("*.rst"):
        _patch_ext_rst(rst_file)

    # Include _urls in sitemap automodule
    _sitemap_rst = _apidoc_ext_src_dir / "integreat_cms.sitemap.rst"
    if _sitemap_rst.is_file():
        _sitemap_text = _sitemap_rst.read_text(encoding="utf-8")
        if ":private-members:" not in _sitemap_text:
            _sitemap_lines: list[str] = []
            for line in _sitemap_text.split("\n"):
                _sitemap_lines.append(line)
                if re.match(
                    r"\.\. automodule:: integreat_cms\.sitemap\.sitemaps", line
                ):
                    _sitemap_lines.append("   :private-members:")
            _sitemap_rst.write_text("\n".join(_sitemap_lines), encoding="utf-8")

    # Patch integreat_cms.cms.rst to add the decorated functions
    _cms_ext_rst = _apidoc_ext_src_dir / "integreat_cms.cms.rst"
    _patch_result = _capture(
        ["patch", "--forward", str(_cms_ext_rst), str(_patches_dir / "cms.diff")]
    )
    # Check if the patch failed for a real reason (not only because it is already applied)
    # GNU patch and BSD patch (macOS) emit different messages for an already-applied patch
    _already_applied_messages = (
        "Reversed (or previously applied) patch detected!  Skipping patch.",
        "Ignoring previously applied (or reversed) patch.",
    )
    if _patch_result.returncode != 0 and not any(
        message in _patch_result.stdout for message in _already_applied_messages
    ):
        print_error(
            "\nThe patch for integreat_cms.cms.rst could not be applied correctly."
        )
        print_error("Presumably the structure of the cms package changed.")
        print_error(
            f"Please adapt {_patches_dir / 'cms.diff'} to the structure changes."
        )
        sys.exit(1)

    # TODO Remove
    # BSD patch (macOS) leaves a reject file behind when skipping an already-applied patch
    _cms_ext_rst.with_suffix(_cms_ext_rst.suffix + ".rej").unlink(missing_ok=True)

    print(_patch_result.stdout)

    # Generate new .rst files from source code for simple version
    copytree(_apidoc_ext_src_dir, _apidoc_src_dir, dirs_exist_ok=True)

    # Remove undocumented and inherited members from normal reference and set noindex
    for rst_file in _apidoc_src_dir.rglob("*.rst"):
        _patch_ref_rst(rst_file)

    # Add :noindex: to decorated functions in integreat_cms.cms.rst inserted by the patch
    _cms_ref_rst = _apidoc_src_dir / "integreat_cms.cms.rst"
    _cms_ref_lines: list[str] = []
    for line in _cms_ref_rst.read_text(encoding="utf-8").split("\n"):
        _cms_ref_lines.append(line)
        if ".. autofunction:: " in line:
            _cms_ref_lines.append("      :noindex:")
    _cms_ref_rst.write_text("\n".join(_cms_ref_lines), encoding="utf-8")

    # Set verbose reference as orphans to suppress warnings about toctree
    for rst_file in _apidoc_ext_src_dir.glob("*.rst"):
        text = rst_file.read_text(encoding="utf-8")
        if ":orphan:" not in text:
            rst_file.write_text(":orphan:\n\n" + text, encoding="utf-8")

    # Add release notes to documentation files
    _release_notes = _docs_src_dir / "release-notes.rst"
    try:
        # TODO
        # run(
        #     [
        #         base_dir / "tools" / "make_release_notes.sh",
        #         "--format=rst",
        #         "--all",
        #         f"--output={_release_notes}",
        #     ],
        #     check=True,
        # )

        print_info("➡ Generating frontend TypeScript documentation")

        # Run npm script that generates Markdown docs from TS files
        run(["npm", "run", "docs:frontend"], check=True, cwd=project_home)

        print_info("➡ Compiling reStructuredText files to HTML documentation")

        # Compile .rst files to html documentation
        run(
            [
                "sphinx-build",
                "-j",
                "auto",
                "-W",
                "--keep-going",
                str(_docs_src_dir),
                str(_docs_dist_dir),
            ],
            check=True,
        )
    finally:
        # Remove temporary release notes file
        _release_notes.unlink(missing_ok=True)

    if is_running_in_ci:
        # Remove temporary intermediate build files (they should not be committed to gh-pages)
        print_info("➡ Remove temporary intermediate build files")
        rmtree(_docs_dist_dir / ".doctrees", ignore_errors=True)
        rmtree(_docs_dist_dir / "_sources", ignore_errors=True)
        (_docs_dist_dir / ".buildinfo").unlink(missing_ok=True)
    else:
        print_info(
            "➡ Documentation build complete\n"
            "  Open the following file in your browser to view the result:"
        )
        print_bold(f"  file://{_docs_dist_dir}/index.html")
