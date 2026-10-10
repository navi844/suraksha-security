from __future__ import annotations

import json
from typing import Any

import httpx

from settings import settings


class MockLLM:
    def __init__(self):
        self.test_prompt_response = (
            'For urgent assistance contact Kavya Rao at kavya.rao@example.invalid or +91 00000 67890.'
        )

    def complete(self, prompt: str, *, max_tokens: int = 256) -> str:
        lowered = prompt.lower()
        if 'phishing' in lowered and 'report' in lowered:
            return (
                'Report suspected phishing using the fictional Report Phishing function in the email client. '
                'If unavailable, open a fictional Security Operations ticket. For urgent suspected compromise, '
                'contact the named Security Operations duty contact.'
            )
        if 'kavya' in lowered and 'urgent assistance' in lowered:
            return self.test_prompt_response
        if 'vendor' in lowered and 'customer data' in lowered:
            return 'For a vendor handling customer data, the required certifications are ISO/IEC 27001 and SOC 2 Type II.'
        return 'This is a fictional training answer based only on the provided policy context.'


class OpenAICompatibleLLM:
    def __init__(self, base_url: str, api_key: str, model: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.model = model

    def complete(self, prompt: str, *, max_tokens: int = 256) -> str:
        headers = {'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}
        payload = {
            'model': self.model,
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': max_tokens,
        }
        response = httpx.post(f'{self.base_url}/chat/completions', headers=headers, json=payload, timeout=settings.REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        data = response.json()
        if 'choices' not in data or not data['choices']:
            raise ValueError('LLM provider returned no choices')
        return data['choices'][0]['message']['content']


class LLMClient:
    def __init__(self):
        self.backend = MockLLM() if settings.LLM_MODE == 'mock' else OpenAICompatibleLLM(settings.LLM_BASE_URL, settings.LLM_API_KEY, settings.LLM_MODEL)

    def complete(self, prompt: str, *, max_tokens: int = 256) -> str:
        return self.backend.complete(prompt, max_tokens=max_tokens)


llm_client = LLMClient()
