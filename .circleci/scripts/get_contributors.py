#!/usr/bin/env python3

import argparse
import json
import logging
import requests

# Init logging config
logging.basicConfig(format="%(message)s")
logger = logging.getLogger(__name__)


def parse_args():
    """
    Parse the given command line arguments

    :returns: The command line arguments
    :rtype: str
    """

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Get contributors between two given git references"
    )
    parser.add_argument("token", metavar="TOKEN", help="GitHub API token")
    parser.add_argument("base", metavar="BASE", help="the base branch/tag/commit")
    parser.add_argument("head", metavar="HEAD", help="the head branch/tag/commit")
    parser.add_argument(
        "-v", "--verbose", action="count", default=0, help="increase logging verbosity"
    )
    args = parser.parse_args()

    # Set logging verbosity
    if args.verbose == 1:
        logger.setLevel(logging.INFO)
    elif args.verbose == 2:
        logger.setLevel(logging.DEBUG)

    return args


def get_commits(token, base, head):
    """
    Get the commits between the to references ``base`` and ``head``

    :param token: The access token for the GitHub API
    :type token: str

    :param base: The base git reference
    :type base: str

    :param head: The head git reference
    :type head: str

    :raises SystemExit: When the API returns an error

    :returns: The list of commits
    :rtype: list
    """
    # Get the commits since the last tag
    another_page = True
    endpoint = f"https://api.github.com/repos/digitalfabrik/integreat-cms/compare/{base}...{head}?per_page=100"
    commits = []

    # Retrieve commits as long as other pages exist
    while another_page:
        # Request GitHub API
        logger.info("Retrieving endpoint: %r", endpoint)
        response = requests.get(
            endpoint,
            headers={"Authorization": f"token {token}"},
            timeout=60,
        )
        if not response.ok:
            logger.error(
                "Fetching commits failed with status %r and content %s",
                response.status_code,
                json.dumps(response.json(), indent=2),
            )
            raise SystemExit(1)
        logger.debug("Response: %s", json.dumps(response.json(), indent=2))
        # Append to commit list
        commits.extend(response.json()["commits"])
        # Check if there is another page of commits
        if "next" in response.links:
            endpoint = response.links["next"]["url"]
        else:
            another_page = False

    if not commits:
        logger.error("No commits found")
        raise SystemExit(1)

    logger.debug("Commits: %s", json.dumps(commits, indent=2))
    return commits


def get_authors(commits):
    """
    Get a list of authors of a list of commits

    :param commits: The list of commits
    :type commits: list

    :raises SystemExit: When the commits do not contain a valid author

    :returns: The list of authors
    :rtype: list
    """
    authors = []
    for commit in commits:
        # Skip anonymous authors
        if not commit["author"]:
            continue
        username = commit["author"]["login"]
        # Skip the bot
        if username == "deliverino[bot]":
            continue
        # Once is enough
        if username in authors:
            continue
        # Append author
        authors.append(username)

    if not authors:
        logger.error("No authors found")
        raise SystemExit(1)

    logger.info("Authors: %r", authors)
    return authors


def main():
    """
    Get the contributors between two given git references

    :raises SystemExit: When something went wrong
    """
    # Parse command line arguments
    args = parse_args()

    # Get list of commits between the given git references
    commits = get_commits(token=args.token, base=args.base, head=args.head)

    # Get list of authors in the given commits
    authors = get_authors(commits)

    # Print out the usernames of all contributors
    print("@" + " @".join(authors))


if __name__ == "__main__":
    main()
