"""
Render the query report as a static HTML page (HTML and CSS only)
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from django.template import Context, Engine

if TYPE_CHECKING:
    from typing import Final

    from .analysis import Report

#: The directory containing the report template
TEMPLATE_DIR: Final = Path(__file__).resolve().parent / "templates"
#: The number of tests listed in the report (the JSON contains all of them)
HTML_TESTS: Final = 200


def render_html(report: Report) -> str:
    """
    Render the report with a standalone template engine, independent of the project's template settings.

    :param report: The merged report
    :return: The HTML page
    """
    engine = Engine(dirs=[str(TEMPLATE_DIR)])
    template = engine.get_template("query_report.html")

    return template.render(
        Context(
            {
                "report": report,
                "tests": report["tests"][:HTML_TESTS],
                "html_tests": HTML_TESTS,
            }
        )
    )
