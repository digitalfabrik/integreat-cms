"""
Zammad API helper functions
"""

import requests

from ..models import Region

def zammad_request(
        method: str, region: Region, path: str, payload: dict = None
    ) -> requests.Response:
    """
    Wrapper for calling the Zammad API. Mostly takes care of auth and timeout.
    
    :param method: HTTP Method
    :param region: Region to which the chat/Zammad belongs
    :param path: API path that will be called
    :param payload: JSON payload as dict
    :return: Response from Zammad API
    """
    return requests.request(
            method=method,
            url=f"{region.zammad_url}{path}",
            timeout=5,
            headers={'Authorization': region.zammad_access_token},
            json=payload
        )

def get_zammad_user_mail(region: Region) -> str:
    """
    Get Zammad user e-mail

    :param region: region that is connected to the Zammad server
    :return: User e-mail address
    """
    return zammad_request("GET", region, "/api/v1/users/me").json()["login"]
