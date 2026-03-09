# Cloud Deployment Guide

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                    CLOUD LAYER                       │
│                                                      │
│  Cloud Agent (cloud_agent.py)                        │
│    • Monitors shared vault                           │
│    • Processes safe tasks autonomously               │
│    • Delegates sensitive tasks to local HITL         │
│                                                      │
│  Sync Manager (sync_manager.py)                      │
│    • Bidirectional sync: local ↔ cloud storage       │
│    • Backends: Local mirror | AWS S3 | GCS           │
│    • MD5 hash-based change detection                 │
└──────────────────┬───────────────────────────────────┘
                   │   Shared Vault (S3 / GCS / Mount)
                   │
┌──────────────────▼───────────────────────────────────┐
│                  LOCAL LAYER                         │
│                                                      │
│  Ralph Wiggum Orchestrator                           │
│  Claude Agent (claude_agent.py)                      │
│  HITL Approval System                                │
│  MCP Tool Servers                                    │
└──────────────────────────────────────────────────────┘
```

---

## Local Demo (No Cloud Account Needed)

```bash
# Uses local mirror directory automatically
python -m cloud.sync_manager

# Start cloud agent pointing at local vault
CLOUD_VAULT_PATH=./AI_Employee_Vault python -m cloud.cloud_agent
```

---

## AWS S3 Deployment

### 1. Create S3 Bucket

```bash
aws s3 mb s3://your-ai-employee-vault
aws s3api put-bucket-versioning \
  --bucket your-ai-employee-vault \
  --versioning-configuration Status=Enabled
```

### 2. Configure .env

```env
SYNC_BACKEND=s3
S3_BUCKET=your-ai-employee-vault
S3_PREFIX=vault/
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_DEFAULT_REGION=us-east-1
```

### 3. Install Dependencies

```bash
pip install boto3
```

### 4. Run Sync Manager

```bash
python -m cloud.sync_manager
```

---

## EC2 / Cloud VM Deployment

```bash
# On your cloud VM:
git clone <repo>
cd AI_Employee_Vault_IsmatFatima_Platinum_Hackathon0
pip install -r requirements.txt
cp .env.example .env
# Configure .env

# Run cloud agent
CLOUD_VAULT_PATH=/mnt/shared-vault python -m cloud.cloud_agent
```

---

## Docker Deployment

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
ENV PYTHONUNBUFFERED=1
CMD ["python", "-m", "cloud.cloud_agent"]
```

```bash
docker build -t ai-employee-cloud .
docker run -d \
  --env-file .env \
  -v /path/to/vault:/app/AI_Employee_Vault \
  ai-employee-cloud
```

---

## Security Notes

- Never store credentials in Docker images
- Use IAM roles on AWS (avoid access key files)
- Enable S3 bucket encryption at rest
- Restrict S3 bucket policy to specific IAM roles
- Use VPC endpoints for S3 access in production
