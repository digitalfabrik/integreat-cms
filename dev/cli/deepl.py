import requests


def deepl_translate(
    auth_key: str, source_lang: str, target_lang: str, text: str
) -> str:
    # Check if the key belongs to a free or pro account
    deepl_api = (
        "https://api-free.deepl.com"
        if auth_key.endswith(":fx")
        else "https://api.deepl.com"
    )
    response = requests.post(
        f"{deepl_api}/v2/translate",
        headers={"Authorization": f"DeepL-Auth-Key {auth_key}"},
        data={
            "source_lang": source_lang,
            "target_lang": target_lang,
            "text": text,
        },
        timeout=30,
    )
    response.raise_for_status()

    return response.json()["translations"][0]["text"]
