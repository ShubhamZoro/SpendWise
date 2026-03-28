import base64
import os
from typing import Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class OCRService:
    def __init__(self, api_key: Optional[str] = None):
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o"

    def extract_receipt_data(self, image_base64: str) -> Dict[str, Any]:
        prompt = """Analyze this receipt image and extract the following information in JSON format:
        {
            "amount": <total amount as number>,
            "date": <date in YYYY-MM-DD format>,
            "category": <one of: food, groceries, transport, entertainment, utilities, healthcare, education, shopping, other>,
            "notes": <any additional details like store name, items purchased>,
            "confidence": <confidence score between 0 and 1>,
            "raw_text": <any text that couldn't be parsed>
        }
        
        If you cannot read the receipt clearly, still provide your best guess and set confidence accordingly.
        If no receipt is detected, return: {"error": "No receipt detected", "confidence": 0}
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                },
                            },
                        ],
                    }
                ],
                max_tokens=500,
            )

            content = response.choices[0].message.content

            import json
            import re

            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return result
            else:
                return {
                    "error": "Could not parse receipt data",
                    "raw_response": content,
                    "confidence": 0,
                }

        except Exception as e:
            return {"error": str(e), "confidence": 0}

    def validate_extracted_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        required_fields = ["amount", "date", "category"]
        missing_fields = [
            f for f in required_fields if f not in data or data[f] is None
        ]

        if missing_fields:
            data["validation_errors"] = f"Missing fields: {', '.join(missing_fields)}"
            data["is_valid"] = False
        else:
            data["is_valid"] = True

        if "amount" in data:
            try:
                data["amount"] = float(data["amount"])
                if data["amount"] < 0:
                    data["amount"] = abs(data["amount"])
            except (ValueError, TypeError):
                data["amount"] = 0
                data["validation_errors"] = "Invalid amount format"
                data["is_valid"] = False

        return data


ocr_service = OCRService()
