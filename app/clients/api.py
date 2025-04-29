import requests

from app.config import settings

def get_token(oauth_token) -> str:
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
    """
    Отправляет запрос к Yandex GPT API

    :param folder_id: Идентификатор каталога Yandex Cloud
    :param iam_token: IAM-токен для аутентификации
    :param prompt_text: Текст запроса пользователя
    :param system_prompt: Системный промпт (опционально)
    :param temperature: Креативность ответа (0-1)
    :param max_tokens: Максимальное количество токенов в ответе
    :return: Ответ от API в виде строки
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
