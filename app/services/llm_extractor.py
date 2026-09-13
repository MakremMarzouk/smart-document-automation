import json
import httpx
from app.core.config import settings
from app.schemas.extracted_data import InvoiceData

class LLMExtractor:
    @staticmethod
    def extract_invoice_data(raw_text: str) -> dict:
        """
        Sends the document text to local Ollama LLM and requests
        a structured JSON response matching the InvoiceData schema.
        """
        prompt = f"""
You are an expert invoice extraction AI. Extract the invoice information from the provided document text.

Document Text:
\"\"\"
{raw_text}
\"\"\"

Return a valid JSON object matching this schema:
{{
  "invoice_number": string or null,
  "vendor_name": string or null,
  "customer_name": string or null,
  "invoice_date": string (YYYY-MM-DD) or null,
  "due_date": string (YYYY-MM-DD) or null,
  "currency": string (e.g. USD, EUR, GBP),
  "items": [
    {{
      "description": string,
      "quantity": float or null,
      "unit_price": float or null,
      "total_price": float or null
    }}
  ],
  "subtotal": float or null,
  "tax_amount": float or null,
  "total_amount": float or null
}}

Only respond with the JSON object. Do not include markdown formatting, backticks, or any conversational text.
"""

        try:
            # Call the local Ollama API (running on your Mac)
            response = httpx.post(
                f"{settings.OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": settings.OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"  # Forces Ollama to strictly return valid JSON
                },
                timeout=60.0  # Allow up to 60s for local inference
            )
            response.raise_for_status()
            
            result = response.json()
            response_text = result.get("response", "{}")
            
            # Parse and validate with our Pydantic schema
            parsed_json = json.loads(response_text)
            invoice_data = InvoiceData(**parsed_json)
            
            return invoice_data.model_dump()

        except httpx.ConnectError:
            raise RuntimeError(
                f"Could not connect to Ollama at {settings.OLLAMA_BASE_URL}. "
                "Make sure the Ollama app is running on your Mac!"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to extract structured data via LLM: {str(e)}")