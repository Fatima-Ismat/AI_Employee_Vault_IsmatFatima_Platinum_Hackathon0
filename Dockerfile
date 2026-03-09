# ── Hugging Face Spaces — Docker Deployment ───────────────────────────────────
# Deploys the FastAPI backend on port 7860 (required by HF Spaces).
#
# Space: https://huggingface.co/spaces/ismat110/ai-employee-vault-ismat-platinum
# Start: uvicorn backend.main:app --host 0.0.0.0 --port 7860

FROM python:3.11-slim

# HF Spaces requires port 7860
EXPOSE 7860

WORKDIR /app

# Install only backend dependencies (no watchers / playwright / cloud SDKs)
COPY requirements-hf.txt .
RUN pip install --no-cache-dir -r requirements-hf.txt

# Copy source packages the backend depends on
COPY backend/     backend/
COPY utils/       utils/
COPY analytics/   analytics/

# Create vault directory structure so the backend can read/write tasks
RUN mkdir -p \
    AI_Employee_Vault/Inbox \
    AI_Employee_Vault/Needs_Action \
    AI_Employee_Vault/Plans \
    AI_Employee_Vault/Pending_Approval \
    AI_Employee_Vault/Approved \
    AI_Employee_Vault/Rejected \
    AI_Employee_Vault/Done \
    AI_Employee_Vault/Logs \
    history

# Copy existing vault content (tasks, briefings, logs) if present
COPY AI_Employee_Vault/ AI_Employee_Vault/
COPY history/           history/

# Environment defaults — override via HF Spaces Secrets
ENV DEMO_MODE=true
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# HF Spaces runs as a non-root user; ensure dirs are writable
RUN chmod -R 777 AI_Employee_Vault history

# Start the FastAPI backend on port 7860
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
