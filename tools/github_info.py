#!/usr/bin/env python

"""
Fetch information on issue or pull request from GitHub
Use JSON embedded for react frontend on pages served to browser
to stay zero-config (no API key/token to create)
"""

# ruff: noqa: PLW0603, T201

import hashlib
import json
import re
import shlex
import sys

import requests
from lxml.html import fromstring

from typing import Any


#################################################################
# ALL OUTPUT of this script is supposed to be machine readable. #
# Warnings NEED to go to stderr so the shell doesn't abort!     #
#################################################################


# Get repo/issue to look up from arguments
args = dict(enumerate(sys.argv))

ORG = args.get(4, "digitalfabrik")
PROJECT = args.get(3, "integreat-cms")
TYPE = args.get(2, "ISSUE").upper()
NUMBER = int(n) if (n := args.get(1)) is not None else None

URL = None


def validate_args(org: str, project: str, typ: str, number: int | None) -> str:
    # Number is required, providing a default would not make sense
    if number is None:
        raise ValueError("Oops! You need to provide an issue/pull number to look up")

    # Build the endpoint URL to fetch
    url = f"https://github.com/{org}/{project}"
    if typ == "ISSUE":
        url += f"/issues/{number}"
    elif typ == "PULL":
        url += f"/pull/{number}"
    else:
        raise ValueError(f"Oops! Unknown type {typ} (not ISSUE or PULL)")

    global URL
    URL = url
    return url


def fetch_page(url: str) -> requests.Response:
    global ORG, PROJECT, TYPE, NUMBER, URL

    r = requests.get(url, timeout=30)

    # Validate answer
    if r.status_code != 200:
        raise ValueError(f"Oops! Got status code {r.status_code}")
    if (mime := r.headers["content-type"].split(";")[0]) != "text/html":
        raise ValueError(f"Oops! Got unexpected mime type {mime}")

    if r.url != url:
        # We were redirected, find out where and whether it is a valid target we can switch to
        match = re.fullmatch(
            r"(?P<proto>.*)://(?P<domain>[^/]+)/(?P<org>[^/]+)/(?P<project>[^/]+)/(?P<type>[^/]+)/(?P<number>[0-9]+)",
            r.url,
        )
        if match is None:
            raise ValueError(
                f"Oops! Redirect to URL I don't know how to interpret: {r.url}"
            )
        if match.group("domain") != "github.com":
            print(
                f"Warning: Redirected to other domain: {match.group('domain')} ({r.url})",
                file=sys.stderr,
            )
        if match.group("org") != ORG:
            ORG = match.group("org")
            print(
                f"Warning: Redirected to other organization/user: {match.group('domain')} ({r.url})",
                file=sys.stderr,
            )
        if match.group("project") != PROJECT:
            PROJECT = match.group("project")
            print(
                f"Warning: Redirected to other project: {match.group('domain')} ({r.url})",
                file=sys.stderr,
            )
        if match.group("type") != f"{TYPE.lower()}s":
            TYPE = match.group("type").removesuffix("s").upper()
            if TYPE not in ["ISSUE", "PULL"]:
                raise ValueError(f"Oops! Redirected to unknown type: {TYPE} ({r.url})")
            print(
                f"Warning: Redirected to other type: {TYPE} ({r.url})", file=sys.stderr
            )
        if match.group("number") != str(NUMBER):
            NUMBER = int(match.group("number"))
            print(
                f"Warning: Redirected to other number: {NUMBER}, ({r.url})",
                file=sys.stderr,
            )

        # No critical problems, take this as the new URL
        URL = r.url

    return r


def parse_data(r: requests.Response) -> dict[str, Any]:
    # Parse the HTML returned by GitHub
    root = fromstring(r.text)

    # Locate data block: <script type="application/json" data-target="react-app.embeddedData">
    # Equivalent of:  script = root.cssselect('script[data-target="react-app.embeddedData"]')
    script = root.xpath(
        "descendant-or-self::script[@data-target = 'react-app.embeddedData']"
    )

    if len(script) == 0:
        raise ValueError("Oops! Couldn't find data block on page")
    if len(script) > 1:
        print(
            "Warning: Multiple data block found on page, just using the first one",
            file=sys.stderr,
        )

    # Parse data block
    return json.loads(script[0].text)


def extract_data(data: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    # Extract important information
    target_data = {}
    extra_data = {}

    # Unfortunately these formats vary wildly by type
    if TYPE == "ISSUE":
        target_data = data.get("payload", {}).get("structured_data", {})
        # Jump some hoopy to get the desired data
        preloaded_queries = data.get("payload", {}).get("preloadedQueries", [])
        queries = [
            q
            for q in preloaded_queries
            if q.get("queryName", None) == "IssueViewerViewQuery"
        ]
        if queries:
            extra_data = (
                queries[0]
                .get("result", {})
                .get("data", {})
                .get("repository", {})
                .get("issue", {})
            )
    if TYPE == "PULL":
        target_data = (
            data.get("payload", {})
            .get("pullRequestsLayoutRoute", {})
            .get("pullRequest", {})
        )

    return target_data, extra_data


def transform_data(
    target_data: dict[str, Any], extra_data: dict[str, Any]
) -> dict[str, Any]:
    # Now take the gathered data and present it as shell readable variables

    # First the "request" parameters
    g = globals()
    OUT = {
        key: value
        for key in ["ORG", "PROJECT", "TYPE", "NUMBER"]
        if (value := g.get(key)) is not None
    }

    # Then the fetched parameters
    if TYPE == "ISSUE":
        OUT |= (
            {  # Keys to adopt as-is
                key: value
                for key in ["headline", "articleBody", "datePublished", "url"]
                if (value := target_data.get(key)) is not None
            }
            | {  # Nested keys to adopt under a single name
                key: value
                for key, a, b in [
                    ("author", "author", "name"),
                    (
                        "interactionCount",
                        "interactionStatistic",
                        "userInteractionCount",
                    ),
                ]
                if (value := target_data.get(a, {}).get(b, None)) is not None
            }
            | {  # Keys from extra_data to adopt as-is
                key: value
                for key in [
                    "number",
                    "title",
                    "titleHTML",
                    "body",
                    "bodyHTML",
                    "url",
                    "createdAt",
                    "updatedAt",
                    "state",
                    "stateReason",
                    "locked",
                    "isPinned",
                ]
                if (value := extra_data.get(key)) is not None
            }
            | {  # Nested keys from extra_data to adopt under a single name
                key: value
                for key, a, b in [
                    ("issueType", "issueType", "name"),
                    ("issueTypeDescription", "issueType", "description"),
                    ("milestone", "milestone", "title"),
                    ("milestoneDueOn", "milestone", "dueOn"),
                    ("milestoneProgressPercentage", "milestone", "progressPercentage"),
                    ("milestoneClosed", "milestone", "closed"),
                    ("milestoneClosedAt", "milestone", "closedAt"),
                    ("milestoneUrl", "milestone", "url"),
                ]
                if (value := extra_data.get(a, {}).get(b, None)) is not None
            }
            | {  # Arrays to build
                "labels": [
                    value
                    for edge in extra_data.get("labels", {}).get("edges", [])
                    if (value := edge.get("node", {}).get("name", None)) is not None
                ],
                "assigned": [
                    value
                    for node in extra_data.get("assignedActors", {}).get("nodes", [])
                    if (value := node.get("login", None)) is not None
                ],
            }
        )

    elif TYPE == "PULL":
        OUT |= {  # Keys to adopt as-is
            key: target_data.get(key)
            for key in [
                "number",
                "title",
                "state",
                "commitsCount",
                "baseBranch",
                "headBranch",
                "headSha",
                "createdTime",
                "closedTime",
                "mergedTime",
                "mergedBy",
                "headRepositoryName",
                "headRepositoryOwnerLogin",
            ]
        } | {  # Nested keys to adopt under a single name
            key: target_data.get(a, {}).get(b, None)
            for key, a, b in [
                ("author", "author", "login"),
            ]
        }

    return OUT


def print_data(values: dict[str, Any]) -> None:
    # Don't forget to add the shebang indicating it as a shell script
    print("#!/bin/sh")

    for key, value in values.items():
        print_shvar(key, value)


def print_shvar(key: str, value: Any) -> None:
    """
    Present variables in shell form, properly escaping values
    """
    # Handle arrays
    if type(value) in (tuple, list):
        indent = "\n    "
        lines = indent.join([shlex.quote(v) for v in value])
        print(f"{key}=({indent}{lines}\n)")
        return

    value = str(value)
    if "\n" in value:
        # Since the value contains a line break, the most readable approach is to use heredoc
        marker = "EOM"
        # Ensure the marker is actually unique
        while marker in value:
            marker += hashlib.sha256(value.encode()).hexdigest()
        # Write it out,
        # without allowing shell expansion (placing quotes around the start marker) and
        # without causing the shell script to abort after executing read for some reason (|| true)
        print(f"read -r -d '' {key} <<'{marker}' || true\n{value}\n{marker}")
    else:
        # Default case, just use simple variable declaration
        print(f"{key}={shlex.quote(value)}")


def main() -> None:
    URL = validate_args(ORG, PROJECT, TYPE, NUMBER)
    r = fetch_page(URL)
    data = parse_data(r)
    [target_data, extra_data] = extract_data(data)
    transformed = transform_data(target_data, extra_data)
    print_data(transformed)


if __name__ == "__main__":
    main()
