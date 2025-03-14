from __future__ import annotations

import hashlib
import secrets


def generate_random_hash() -> str:
    """
    Generate a random hash. Produces output of length 64.

    :return: The generated random hash
    """
    return hashlib.sha256(secrets.token_bytes(512)).hexdigest()
