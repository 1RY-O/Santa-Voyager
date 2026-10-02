from __future__ import annotations

import json
import os
import re
from abc import ABC, abstractmethod
from typing import Any, Optional

import requests


class AIProvider(ABC):
    """Abstract base class for AI providers (Nebius/NVIDIA or Demo mode)."""

    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str:
        pass

    @abstractmethod
    def parse_json(self, text: str) -> Any:
        pass


DEFAULT_NEBIUS_MODEL = os.getenv(
    "NEBIUS_MODEL", "meta-llama/Meta-Llama-3.1-70B-Instruct"
)


def extract_json(text: str) -> Any:
    """Parse raw JSON, fenced ```json blocks, or embedded objects gracefully."""
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass
    match = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if match:
        return json.loads(match.group(1).strip())
    # Last resort: largest {...} substring
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return json.loads(text[start : end + 1])
    raise ValueError("AI response did not contain valid JSON.")


class NebiusProvider(AIProvider):
    """Provider for Nebius AI Studio (OpenAI-compatible chat completions)."""

    def __init__(
        self,
        api_key: str,
        endpoint: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.api_key = api_key
        self.endpoint = (
            endpoint
            or os.getenv(
                "NEBIUS_API_ENDPOINT",
                "https://api.studio.nebius.com/v1/chat/completions",
            )
        )
        self.model = model or DEFAULT_NEBIUS_MODEL

    def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str:
        # NOTE: API key is sent over HTTPS only and never logged or shown in UI.
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "response_format": {"type": "json_object"},
        }
        response = requests.post(self.endpoint, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

    def parse_json(self, text: str) -> Any:
        return extract_json(text)


class DemoProvider(AIProvider):
    """Deterministic demo provider with hardcoded sample outputs."""

    def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str:
        # Extract key constraints from the user prompt for realistic demo output
        return self._make_demo_response(system_prompt, user_prompt)

    def parse_json(self, text: str) -> Any:
        return extract_json(text)

    def _make_demo_response(self, system_prompt: str, user_prompt: str) -> str:
        # Parse the user prompt to understand constraints for realistic demo
        # Gift demo
        if "gift" in system_prompt.lower() or "gift" in user_prompt.lower():
            return json.dumps({
                "title": "Custom Engraved Leather Wallet",
                "estimated_price": "$45-65",
                "constraint_satisfied": "personalized with recipient's initials",
                "personalization_idea": "Engrave their initials and a short meaningful date",
                "categories": ["accessories", "personalized"],
            })
        # Hangout demo
        if "hangout" in system_prompt.lower() or "hangout" in user_prompt.lower():
            return json.dumps({
                "title": "Rooftop Sunset Picnic",
                "vibe": "Relaxed and romantic",
                "activities": [
                    {"name": "Setup picnic blanket", "duration": "15 min"},
                    {"name": "Wine and cheese tasting", "duration": "45 min"},
                    {"name": "Watch sunset", "duration": "30 min"},
                    {"name": "Stargazing", "duration": "60 min"},
                ],
                "budget_breakdown": "$50-75 total",
                "constraints_satisfied": ["budget-friendly", "outdoor", "evening"],
                "assumptions": ["Verify weather and reservation requirements"],
            })
        # Fallback demo
        return json.dumps({
            "title": "Thoughtful Gift or Experience",
            "estimated_price": "$30-50",
            "constraint_satisfied": "selected based on provided preferences",
            "personalization_idea": "Add a personal note or engraving",
            "categories": ["various"],
        })


def is_live_mode(api_key: Optional[str] = None) -> bool:
    """True only when an API key is present and APP_MODE=live. Never logs the key."""
    key = (api_key or os.getenv("NEBIUS_API_KEY") or "").strip()
    return bool(key) and os.getenv("APP_MODE", "demo").lower() == "live"


def create_provider(api_key: Optional[str] = None) -> AIProvider:
    """Factory for the appropriate provider based on available credentials."""
    key = (api_key or os.getenv("NEBIUS_API_KEY") or "").strip()
    if is_live_mode(key):
        return NebiusProvider(key)
    return DemoProvider()
