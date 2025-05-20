import requests

from tokeon_assistant_rest_api.config import settings

def get_token(oauth_token) -> str:
    """Obtain IAM token from Yandex using OAuth token.

        Args:
            oauth_token: OAuth token from Yandex Passport.

        Returns:
            IAM token string if successful, otherwise None.
        """
    url = "https://iam.api.cloud.yandex.net/iam/v1/tokens"
    headers = {"Content-Type": "application/json"}
    data = {"yandexPassportOauthToken": oauth_token}

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json().get("iamToken")
    except requests.exceptions.RequestException as e:
        print(f"Fail to get token: {e}")
        return None

def send_request_to_yagpt(
        iam_token,
        prompt_text,
        system_prompt=None,
        temperature=0.6,
        max_tokens=2000,
        folder_id=settings.ya_gpt.folder_id
) -> str:
    """Send a request to Yandex GPT API and return the generated text.

    Args:
        iam_token: IAM token for authentication.
        prompt_text: User's prompt text.
        system_prompt: Optional system prompt to guide the model.
        temperature: Sampling temperature for creativity (0 to 1).
        max_tokens: Maximum number of tokens in the response.
        folder_id: Yandex Cloud folder ID.

    Returns:
        Generated response text from the API if successful, otherwise None.
    """
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {iam_token}"
    }

    messages = []

    if system_prompt:
        messages.append({
            "role": "system",
            "text": system_prompt
        })

    messages.append({
        "role": "user",
        "text": prompt_text
    })

    data = {
        "modelUri": f"gpt://{folder_id}/yandexgpt-lite/latest",
        "completionOptions": {
            "stream": False,
            "temperature": temperature,
            "maxTokens": str(max_tokens),
            "reasoningOptions": {
                "mode": "DISABLED"
            }
        },
        "messages": messages
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()

        return result['result']['alternatives'][0]['message']['text']
    except requests.exceptions.RequestException as e:
        print(f"Fail to send API request: {e}")
        return None
    except (KeyError, IndexError) as e:
        print(f"Fail to get response: {e}")
        return None
