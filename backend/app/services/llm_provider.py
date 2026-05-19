import json
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from app.config import settings

T = TypeVar("T", bound=BaseModel)


class LLMProviderError(RuntimeError):
    """Raised when a structured LLM call cannot be completed safely."""


class GeminiProvider:
    def __init__(self, api_key: str, model_name: str) -> None:
        self.api_key = api_key
        self.model_name = model_name

    def generate_structured(self, *, system_prompt: str, user_prompt: str, schema: type[T]) -> T:
        if not self.api_key:
            raise LLMProviderError("GEMINI_API_KEY is not configured.")

        try:
            from google import genai
        except ImportError as exc:
            raise LLMProviderError("google-genai is not installed.") from exc

        prompt = (
            f"{system_prompt.strip()}\n\n"
            f"{user_prompt.strip()}\n\n"
            "Return valid JSON only."
        )

        try:
            client = genai.Client(api_key=self.api_key)
            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_json_schema": schema.model_json_schema(),
                    "temperature": 0.2,
                },
            )
        except Exception as exc:
            raise LLMProviderError(f"Gemini request failed: {exc}") from exc

        payload = getattr(response, "text", "") or ""
        if not payload:
            raise LLMProviderError("Gemini returned an empty response.")

        try:
            return schema.model_validate_json(payload)
        except ValidationError:
            try:
                return schema.model_validate(json.loads(payload))
            except Exception as exc:
                raise LLMProviderError("Gemini returned invalid structured JSON.") from exc


def get_default_llm_provider(model_name: str | None = None) -> GeminiProvider:
    return GeminiProvider(
        api_key=settings.GEMINI_API_KEY,
        model_name=model_name or settings.AI_PICKS_MODEL,
    )
