import base64
import json
import re
from pathlib import Path
from typing import Any

import httpx

from app.config import settings
from app.services.llm import FIELDS


class VisionExtractionService:
    async def structure_image(self, file_path: Path, extracted_text: str = "") -> dict[str, Any] | None:
        if not settings.hf_api_key:
            return None

        mime_type = self._mime_type(file_path)
        data_url = f"data:{mime_type};base64,{base64.b64encode(file_path.read_bytes()).decode('ascii')}"
        prompt = (
            "Read this manufacturing machine shop table image. Extract the first filled row as the main record, "
            "and also include all filled rows in a rows array. Return only valid JSON with this shape:\n"
            "{"
            "\"date\": string|null, \"shift\": string|null, \"employee_number\": string|null, "
            "\"operation_code\": string|null, \"machine_number\": string|null, "
            "\"work_order_number\": string|null, \"quantity_produced\": number|null, "
            "\"time_taken_minutes\": number|null, \"rows\": [same fields per row]"
            "}\n"
            "Convert time taken in hours to minutes. Preserve codes carefully. "
            "Shift may appear as I, II, III; keep it as written. "
            f"Optional OCR text, possibly noisy:\n{extracted_text[:2000]}"
        )

        payload = {
            "model": settings.hf_vision_model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                }
            ],
            "temperature": 0.0,
            "max_tokens": 900,
        }
        headers = {"Authorization": f"Bearer {settings.hf_api_key}"}

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post("https://router.huggingface.co/v1/chat/completions", headers=headers, json=payload)
                response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            data = self._json_from_text(content)
            if not data:
                return None
            return self._normalize(data)
        except Exception:
            return None

    def _json_from_text(self, content: str) -> dict[str, Any] | None:
        match = re.search(r"\{.*\}", content, flags=re.S)
        if not match:
            return None
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None

    def _normalize(self, data: dict[str, Any]) -> dict[str, Any]:
        rows = data.get("rows") if isinstance(data.get("rows"), list) else []
        first_row = next((row for row in rows if isinstance(row, dict)), {})
        if first_row:
            normalized = {field: first_row.get(field, data.get(field)) for field in FIELDS}
        else:
            normalized = {field: data.get(field) for field in FIELDS}

        for field in ("quantity_produced", "time_taken_minutes"):
            value = normalized.get(field)
            if isinstance(value, str):
                number = re.search(r"\d+(?:\.\d+)?", value)
                normalized[field] = int(float(number.group(0))) if number else None

        normalized["rows"] = rows
        return normalized

    def _mime_type(self, file_path: Path) -> str:
        suffix = file_path.suffix.lower()
        if suffix in {".jpg", ".jpeg"}:
            return "image/jpeg"
        if suffix == ".png":
            return "image/png"
        if suffix == ".webp":
            return "image/webp"
        return "image/jpeg"
