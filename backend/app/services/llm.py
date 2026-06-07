import json
import re
from typing import Any

import httpx

from app.config import settings


FIELDS = [
    "date",
    "shift",
    "employee_number",
    "operation_code",
    "machine_number",
    "work_order_number",
    "quantity_produced",
    "time_taken_minutes",
]


class LLMExtractionService:
    async def structure_text(self, extracted_text: str) -> dict[str, Any]:
        if settings.hf_api_key:
            result = await self._call_hf_router(extracted_text)
            if result:
                return result
        return self._fallback_parse(extracted_text)

    async def _call_hf_router(self, extracted_text: str) -> dict[str, Any] | None:
        prompt = (
            "Extract a manufacturing operational record from the text. "
            "Return only valid JSON with keys: date, shift, employee_number, operation_code, "
            "machine_number, work_order_number, quantity_produced, time_taken_minutes. "
            "Use null when unknown.\n\n"
            f"Text:\n{extracted_text}"
        )
        payload = {
            "messages": [
                {"role": "system", "content": "You convert noisy OCR text into strict operational JSON."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
            "max_tokens": 500,
        }
        headers = {"Authorization": f"Bearer {settings.hf_api_key}"}
        url = f"https://router.huggingface.co/v1/chat/completions"

        try:
            async with httpx.AsyncClient(timeout=35) as client:
                response = await client.post(url, headers=headers, json={**payload, "model": settings.hf_model})
                response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            return self._json_from_text(content)
        except Exception:
            return None

    def _json_from_text(self, content: str) -> dict[str, Any] | None:
        match = re.search(r"\{.*\}", content, flags=re.S)
        if not match:
            return None
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
        return {field: data.get(field) for field in FIELDS}

    def _fallback_parse(self, text: str) -> dict[str, Any]:
        patterns = {
            "date": r"(\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",
            "shift": r"\bshift[:\s-]*([A-C]|day|night)\b",
            "employee_number": r"\b(?:employee|emp|operator)[:\s-]*([A-Z]*-?\d{2,})\b",
            "operation_code": r"\b(?:operation|op)[:\s-]*([A-Z]+-?\d{2,})\b",
            "machine_number": r"\b(?:machine|mc|cnc)[:\s-]*([A-Z]+-?\d{1,})\b",
            "work_order_number": r"\b(?:work\s*order|wo)[:\s-]*([A-Z]+-?\d{2,}(?:-\d+)?)\b",
            "quantity_produced": r"\b(?:quantity|qty|produced)[:\s-]*(\d{1,6})\b",
            "time_taken_minutes": r"\b(?:time\s*taken|time|minutes|min)[:\s-]*(\d{1,5})\b",
        }
        data: dict[str, Any] = {}
        for field, pattern in patterns.items():
            match = re.search(pattern, text, flags=re.I)
            value: Any = match.group(1) if match else None
            if field in {"quantity_produced", "time_taken_minutes"} and value is not None:
                value = int(value)
            if field == "shift" and isinstance(value, str):
                value = value.upper()
            data[field] = value
        return data
