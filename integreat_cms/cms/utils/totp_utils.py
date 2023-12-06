"""
This module contains helper functions that are used within the TOTP registration and authentication.
"""

from __future__ import annotations

import base64
import io
from typing import TYPE_CHECKING

import pyotp
import qrcode
from django.conf import settings

if TYPE_CHECKING:
    from ..models import User


def generate_totp_qrcode(key: str, user: User) -> str:
    """
    Render event form for HTTP GET requests

    :param key: The required key to generate the QR code
    :param user: The user account that is trying to add TOTP to its account
    :return: The QR code as a base64-encoded string
    """
    qr_string = pyotp.TOTP(key).provisioning_uri(
        name=user.username, issuer_name=settings.BRANDING_TITLE
    )

    img = qrcode.make(qr_string)

    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="PNG")
    img_byte_val = img_byte_arr.getvalue()

    img_base64_string = "data:image/png;base64," + base64.b64encode(
        img_byte_val
    ).decode("utf-8")

    return img_base64_string


def check_totp_code(given_totp_code: str, key: str) -> bool:
    r"""
    Helper method to check the given code with the initial key

    :param given_totp_code: The entered TOTP code form the user
    :param key: The key that is used for the generation of the true code
    :return: True if the given code matches the initiated
    """
    if not key:
        return False
    totp = pyotp.TOTP(key)

    return totp.verify(given_totp_code, valid_window=2)
