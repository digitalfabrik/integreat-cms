#!/usr/bin/env python3

import os
import argparse
import mimetypes
import requests


def main():
    """
    Create a GitHub release
    """

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Create GitHub release")
    parser.add_argument(
        "-p", "--prerelease", action="store_true", help="mark the release as prerelease"
    )
    parser.add_argument("token", metavar="TOKEN", help="GitHub API token")
    parser.add_argument("tag", metavar="TAG", help="tag for the release")
    parser.add_argument(
        "prev_tag", metavar="PREV_TAG", help="the previous tag of the release"
    )
    parser.add_argument(
        "changelog", metavar="CHANGELOG", help="changelog of the release"
    )
    parser.add_argument(
        "assets", metavar="ASSET", help="uploadable asset file", nargs="*"
    )
    args = parser.parse_args()

    # Assemble release body
    logo_url = "https://raw.githubusercontent.com/Integreat/integreat-cms/dea989c557959f688cc2050b4d4f987c47d982ac/.github/logo.png"
    compare_url = "https://github.com/Integreat/integreat-cms/compare"
    body = (
        f"### ![]({logo_url}) integreat-cms `{args.tag}`"
        f"\n\n### Changelog\n\n{args.changelog}\n\n"
        f"Compare changes: [{args.prev_tag} → {args.tag}]({compare_url}/{args.prev_tag}...{args.tag})"
    )

    # Create release
    response = requests.post(
        "https://api.github.com/repos/Integreat/integreat-cms/releases",
        json={
            "tag_name": args.tag,
            "name": args.tag,
            "body": body,
            "prerelease": args.prerelease,
        },
        headers={"Authorization": f"token {args.token}"},
    )
    release = response.json()
    print(f"Created a new release {release['name']}")

    # Upload_url is given in uri-template form.
    upload_url, _, _ = release["upload_url"].partition("{")
    print("Upload url: %r", upload_url)

    # Upload assets
    for filename in args.assets:
        with open(filename, "rb") as file:
            response = requests.post(
                upload_url,
                data=file,
                params={"name": os.path.basename(filename), "label": "integreat-cms"},
                headers={
                    "Authorization": f"token {args.token}",
                    "Content-Type": (
                        mimetypes.guess_type(filename)[0] or "application/octet-stream"
                    ),
                },
            )
        print(f"Uploaded asset {filename}")


if __name__ == "__main__":
    main()
