from __future__ import annotations

import json
from typing import Any

import requests


ZHIPU_CHAT_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"


class ZhipuClient:
    def __init__(self, api_key: str, model: str = "glm-4.7-flash", timeout: int = 180) -> None:
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def infer_relationship(self, prompt: str) -> dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "temperature": 0.2,
            "stream": False,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a biomedical literature assistant. "
                        "Return only valid JSON with the keys "
                        "summary, inference, explanation, evidence_pmids."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        }

        response = requests.post(
            ZHIPU_CHAT_URL,
            headers=headers,
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        return json.loads(content)
