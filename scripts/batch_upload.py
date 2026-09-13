from pathlib import Path

import httpx


API_URL = "http://localhost:8000/upload/auto-background"
INVOICE_FOLDER = Path("storage/incoming")


def main():
    pdf_files = list(INVOICE_FOLDER.glob("*.pdf"))

    if not pdf_files:
        print("No PDF files found.")
        return

    with httpx.Client() as client:
        for pdf_file in pdf_files:
            with pdf_file.open("rb") as invoice:
                response = client.post(
                    API_URL,
                    files={
                        "file": (
                            pdf_file.name,
                            invoice,
                            "application/pdf",
                        )
                    },
                )

            if response.is_success:
                document = response.json()
                print(
                    f"{pdf_file.name}: "
                    f"id={document['id']}, "
                    f"status={document['status']}"
                )
            else:
                print(
                    f"{pdf_file.name}: failed "
                    f"({response.status_code}) {response.text}"
                )


if __name__ == "__main__":
    main()