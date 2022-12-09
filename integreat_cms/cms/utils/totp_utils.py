"""
This module contains helper functions that are used within the TOTP registration and authentication.
"""

import base64
import io
import pyotp
import qrcode

from django.conf import settings


def generate_totp_qrcode(key, user):
    """
    Render event form for HTTP GET requests

    :param key: The required key to generate the QR code
    :type key: str

    :param user: The user account that is trying to add TOTP to its account
    :type user: ~django.contrib.auth.models.User

    :return: The QR code as a base64-encoded string
    :rtype: str
    """
    qr_string = pyotp.TOTP(key).provisioning_uri(
        name=user.username, issuer_name=settings.BRANDING.capitalize()
    )

    img = qrcode.make(qr_string)

    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="PNG")
    img_byte_arr = img_byte_arr.getvalue()

    img_base64_string = "data:image/png;base64," + base64.b64encode(
        img_byte_arr
    ).decode("utf-8")

    return img_base64_string


def check_totp_code(given_totp_code, key):
    r"""
    Helper method to check the given code with the initial key

    :param given_totp_code: The entered TOTP code form the user
    :type given_totp_code: str

    :param key: The key that is used for the generation of the true code
    :type key: str

    :return: True if the given code matches the initiated
    :rtype: bool
    """
    if not key:
        return False
    totp = pyotp.TOTP(key)

    return totp.verify(given_totp_code, valid_window=2)
