#!/usr/bin/env python3

from __future__ import annotations

import argparse
import os
from base64 import b64decode
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

import jwt
import requests

if TYPE_CHECKING:
    from typing import Any


def permission(value: str) -> tuple[str, str]:
    """
    Parse a permission of the form ``NAME=LEVEL``, e.g. ``pull_requests=write``

    :param value: The command line value
    :raises argparse.ArgumentTypeError: If the value is not of the form ``NAME=LEVEL``
    :returns: A tuple of the permission name and level
    """
    name, _, level = value.partition("=")
    if not name or not level:
        raise argparse.ArgumentTypeError(
            f"invalid permission {value!r}, expected NAME=LEVEL"
        )
    return name, level


def parse_args() -> argparse.Namespace:
    """
    :returns: The command line arguments
    """

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Request an installation access token for the Deliverino app",
    )
    parser.add_argument(
        "--repository",
        action="append",
        dest="repositories",
        metavar="NAME",
        help="restrict the token to this repository (can be given multiple times, default: all repositories of the installation)",
    )
    parser.add_argument(
        "--permission",
        action="append",
        dest="permissions",
        type=permission,
        metavar="NAME=LEVEL",
        help="restrict the token to this permission, e.g. pull_requests=write (can be given multiple times, default: all permissions of the app)",
    )
    return parser.parse_args()


def main() -> None:
    """
    This method reads the deliverino private key from the environment variable ``DELIVERINO_PRIVATE_KEY``, generates a
    JSON web token which is valid for 10 minutes, uses this to request an installation access token (which is then valid
    for 1 hour) and prints it to the console. If repositories or permissions are given, the token is restricted to them.

    :raises RuntimeError: If the environment variable ``DELIVERINO_PRIVATE_KEY`` is missing or the token request fails.
    """
    args = parse_args()

    # Get private key from environment (base64 encoded)
    try:
        deliverino_private_key = os.environ["DELIVERINO_PRIVATE_KEY"]
    except KeyError as e:
        raise RuntimeError(
            "Please make sure this step has access to the 'deliverino' CircleCI context.",
        ) from e

    # Generate payload for the JWT
    payload = {
        # issued at time, 60 seconds in the past to allow for clock drift
        "iat": int(datetime.timestamp(datetime.now() - timedelta(minutes=1))),
        # JWT expiration time (10 minute maximum)
        "exp": int(datetime.timestamp(datetime.now() + timedelta(minutes=9))),
        # GitHub App's identifier
        "iss": "59249",
    }

    # Sign payload and encode JWT
    encoded_jwt = jwt.encode(
        payload,
        b64decode(deliverino_private_key),
        algorithm="RS256",
    )

    # Restrict the token (without a body, it gets all repositories and permissions of the installation)
    data: dict[str, Any] = {}
    if args.repositories:
        data["repositories"] = args.repositories
    if args.permissions:
        data["permissions"] = dict(args.permissions)

    # Request access token
    response = requests.post(
        "https://api.github.com/app/installations/16579631/access_tokens",
        headers={"Authorization": f"Bearer {encoded_jwt}"},
        json=data or None,
        timeout=60,
    )
    if not response.ok:
        raise RuntimeError(
            f"Requesting the access token failed with {response.status_code}: {response.text}",
        )

    # Print access token
    print(response.json()["token"])


if __name__ == "__main__":
    main()
