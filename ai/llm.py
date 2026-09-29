import requests


OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "llama3.2:1b"


def ask_llm(prompt):
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "stream": False,
        },
        timeout=120,
    )

    response.raise_for_status()

    data = response.json()

    return data["message"]["content"]
