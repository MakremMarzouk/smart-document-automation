import os
from pypdf import PdfReader

class TextExtractor:
    @staticmethod
    def extract_text(file_path: str) -> str:
        """
        Extracts plain text from a given file (.txt or .pdf).
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        _, ext = os.path.splitext(file_path)
        ext = ext.lower()

        if ext == ".txt":
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()

        elif ext == ".pdf":
            reader = PdfReader(file_path)
            extracted_pages = []
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    extracted_pages.append(text)
            return "\n\n".join(extracted_pages)

        else:
            raise ValueError(f"Unsupported file format for plain text extraction: {ext}")