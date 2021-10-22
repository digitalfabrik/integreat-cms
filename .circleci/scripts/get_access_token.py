#!/usr/bin/env python3

from base64 import b64decode
from datetime import datetime, timedelta

import os
import requests
import jwt


def main():
    """
    This method reads the deliverino private key from the environment variable ``DELIVERINO_PRIVATE_KEY``, generates a
    JSON web token which is valid for 10 minutes, uses this to request an installation access token (which is then valid
    for 1 hour) and prints it to the console.

    :raises RuntimeError: If the environment variable ``DELIVERINO_PRIVATE_KEY`` is missing.
    """

    # Get private key from environment (base64 encoded)
    try:
        deliverino_private_key = os.environ["DELIVERINO_PRIVATE_KEY"]
    except KeyError as e:
        raise RuntimeError(
            "Please make sure this step has access to the 'deliverino' CircleCI context."
        ) from e

    # Generate payload for the JWT
    payload = {
        # issued at time, 60 seconds in the past to allow for clock drift
        "iat": int(datetime.timestamp(datetime.now() - timedelta(minutes=1))),
        # JWT expiration time (10 minute maximum)
        "exp": int(datetime.timestamp(datetime.now() + timedelta(minutes=10))),
        # GitHub App's identifier
        "iss": 59249,
    }

    # Sign payload and encode JWT
    encoded_jwt = jwt.encode(
        payload, b64decode(deliverino_private_key), algorithm="RS256"
    )

    # Request access token
    response = requests.post(
        "https://api.github.com/app/installations/7668676/access_tokens",
        headers={"Authorization": f"Bearer {encoded_jwt}"},
    )

    # Print access token
    print(response.json()["token"])


if __name__ == "__main__":
    main()
