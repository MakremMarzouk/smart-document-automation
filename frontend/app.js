const fileInput = document.getElementById("invoice-file");
const dropZone = document.querySelector(".drop-zone");
const selectedFile = document.getElementById("selected-file");
const uploadButton = document.getElementById("upload-button");
const message = document.getElementById("message");
const resultCard = document.getElementById("result-card");
const resultStatus = document.getElementById("result-status");
const resultId = document.getElementById("result-id");
const resultFilename = document.getElementById("result-filename");
const resultInvoiceNumber = document.getElementById("result-invoice-number");
const resultVendor = document.getElementById("result-vendor");
const resultTotal = document.getElementById("result-total");
const resultErrors = document.getElementById("result-errors");

const API_URL = "http://localhost:8000/upload/auto";
const QUEUE_API_URL = "http://localhost:8000/documents/queue/review";
const DOCUMENTS_API_URL = "http://localhost:8000/documents";

let selectedInvoice = null;

function showMessage(text) {
    message.textContent = text;
    message.classList.remove("hidden");
}

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function selectFile(file) {
    if (!file) {
        return;
    }

    const allowedTypes = ["application/pdf", "text/plain"];

    if (!allowedTypes.includes(file.type)) {
        showMessage("Please select a PDF or text invoice.");
        return;
    }

    selectedInvoice = file;
    selectedFile.textContent = `Selected file: ${file.name}`;
    selectedFile.classList.remove("hidden");
    uploadButton.disabled = false;
    showMessage("");
}

fileInput.addEventListener("change", () => {
    selectFile(fileInput.files[0]);
});

dropZone.addEventListener("dragover", (event) => {
    event.preventDefault();
    dropZone.classList.add("dragging");
});

dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("dragging");
});

dropZone.addEventListener("drop", (event) => {
    event.preventDefault();
    dropZone.classList.remove("dragging");
    selectFile(event.dataTransfer.files[0]);
});

uploadButton.addEventListener("click", async () => {
    if (!selectedInvoice) {
        return;
    }

    uploadButton.disabled = true;
    uploadButton.textContent = "Processing...";
    showMessage("Uploading and processing your invoice...");
    resultCard.classList.add("hidden");

    const formData = new FormData();
    formData.append("file", selectedInvoice);

    try {
        const response = await fetch(API_URL, {
            method: "POST",
            body: formData,
        });

        const document = await response.json();

        if (!response.ok) {
            throw new Error(document.detail || "Upload failed.");
        }

        displayResult(document);
        await loadReviewQueue();
        showMessage("Invoice processed successfully.");
    } catch (error) {
        showMessage(`Error: ${error.message}`);
    } finally {
        uploadButton.disabled = false;
        uploadButton.textContent = "Process invoice";
    }
});

function displayResult(document) {
    const extractedData = document.extracted_data || {};
    const errors = document.validation_errors || [];

    resultId.textContent = document.id;
    resultFilename.textContent = document.filename;
    resultInvoiceNumber.textContent = extractedData.invoice_number || "—";
    resultVendor.textContent = extractedData.vendor_name || "—";
    resultTotal.textContent = extractedData.total_amount
        ? `${extractedData.currency || "USD"} ${extractedData.total_amount}`
        : "—";
    resultErrors.textContent = errors.length
        ? errors.join(", ")
        : "None";

    resultStatus.textContent = document.status;
    resultStatus.className = `status-badge status-${document.status}`;
    resultCard.classList.remove("hidden");
}
const refreshQueueButton = document.getElementById(
    "refresh-queue-button"
);
const queueList = document.getElementById("queue-list");

async function loadReviewQueue() {
    queueList.innerHTML = '<p class="empty-state">Loading review queue...</p>';

    try {
        const response = await fetch(QUEUE_API_URL);

        if (!response.ok) {
            throw new Error("Could not load the review queue.");
        }

        const documents = await response.json();

        if (documents.length === 0) {
            queueList.innerHTML =
                '<p class="empty-state">No invoices currently need review.</p>';
            return;
        }

        queueList.innerHTML = documents
            .map((document) => {
                const errors = document.validation_errors || [];

                return `
                    <article class="queue-item">
                        <div class="queue-item-info">
                            <strong>${escapeHtml(document.filename)}</strong>
                            <span>
                                Invoice:
                                ${escapeHtml(document.extracted_data?.invoice_number || "—")}
                            </span>
                            <span>
                                Vendor:
                                ${escapeHtml(document.extracted_data?.vendor_name || "—")}
                            </span>
                            <span class="queue-error">
                                ${escapeHtml(errors.join(", "))}
                            </span>
                        </div>

                        <div class="queue-actions">
                            <button class="approve-button" data-document-id="${document.id}">
                                Approve
                            </button>

                            <button class="secondary-button correct-button" data-document-id="${document.id}">
                                Correct
                            </button>
                        </div>
                    </article>
                `;
            })
            .join("");
    } catch (error) {
        queueList.innerHTML =
            `<p class="empty-state">Error: ${error.message}</p>`;
    }
}

refreshQueueButton.addEventListener("click", loadReviewQueue);

loadReviewQueue();

queueList.addEventListener("click", async (event) => {
    const correctButton = event.target.closest(".correct-button");

    if (correctButton) {
        const documentId = correctButton.dataset.documentId;

        try {
            const response = await fetch(`${DOCUMENTS_API_URL}/${documentId}`);
            const apiDocument = await response.json();

            if (!response.ok) {
                throw new Error(apiDocument.detail || "Could not load document.");
            }

            const data = apiDocument.extracted_data || {};
            const firstItem = data.items?.[0] || {};

            document.getElementById("correction-document-id").value = apiDocument.id;
            document.getElementById("correction-invoice-number").value = data.invoice_number || "";
            document.getElementById("correction-vendor-name").value = data.vendor_name || "";
            document.getElementById("correction-invoice-date").value = data.invoice_date || "";
            document.getElementById("correction-due-date").value = data.due_date || "";
            document.getElementById("correction-item-description").value = firstItem.description || "Service";
            document.getElementById("correction-item-quantity").value = firstItem.quantity || 1;
            document.getElementById("correction-item-unit-price").value = firstItem.unit_price || 0;
            document.getElementById("correction-subtotal").value = data.subtotal || 0;
            document.getElementById("correction-tax").value = data.tax_amount || 0;
            document.getElementById("correction-total").value = data.total_amount || 0;

            document.getElementById("correction-modal").classList.remove("hidden");
        } catch (error) {
            showMessage(`Error: ${error.message}`);
        }

        return;
    }

    const approveButton = event.target.closest(".approve-button");

    if (!approveButton) {
        return;
    }

    const documentId = approveButton.dataset.documentId;

    approveButton.disabled = true;
    approveButton.textContent = "Approving...";

    try {
        const response = await fetch(
            `http://localhost:8000/documents/${documentId}/review`,
            {
                method: "PATCH",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    action: "approve",
                }),
            }
        );

        const document = await response.json();

        if (!response.ok) {
            throw new Error(document.detail || "Approval failed.");
        }

        showMessage(`Document ${documentId} approved.`);
        await loadReviewQueue();
    } catch (error) {
        showMessage(`Error: ${error.message}`);
        approveButton.disabled = false;
        approveButton.textContent = "Approve";
    }
});

const correctionModal = document.getElementById("correction-modal");
const closeModalButton = document.getElementById("close-modal-button");
const correctionForm = document.getElementById("correction-form");

closeModalButton.addEventListener("click", () => {
    correctionModal.classList.add("hidden");
});

correctionForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const documentId = document.getElementById("correction-document-id").value;
    const quantity = Number(document.getElementById("correction-item-quantity").value);
    const unitPrice = Number(document.getElementById("correction-item-unit-price").value);

    const correctedData = {
        invoice_number: document.getElementById("correction-invoice-number").value,
        vendor_name: document.getElementById("correction-vendor-name").value,
        invoice_date: document.getElementById("correction-invoice-date").value,
        due_date: document.getElementById("correction-due-date").value || null,
        currency: "USD",
        items: [
            {
                description: document.getElementById("correction-item-description").value,
                quantity,
                unit_price: unitPrice,
                total_price: quantity * unitPrice,
            },
        ],
        subtotal: Number(document.getElementById("correction-subtotal").value),
        tax_amount: Number(document.getElementById("correction-tax").value),
        total_amount: Number(document.getElementById("correction-total").value),
    };

    try {
        const response = await fetch(`${DOCUMENTS_API_URL}/${documentId}/review`, {
            method: "PATCH",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                action: "correct",
                extracted_data: correctedData,
            }),
        });

        const document = await response.json();

        if (!response.ok) {
            throw new Error(document.detail || "Correction failed.");
        }

        correctionModal.classList.add("hidden");
        showMessage(`Document ${documentId} corrected and revalidated.`);
        displayResult(document);
        await loadReviewQueue();
    } catch (error) {
        showMessage(`Error: ${error.message}`);
    }
});
