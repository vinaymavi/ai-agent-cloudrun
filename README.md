# 🚀 How to Deploy an AI Agent on Google Cloud Run Using Artifact Registry and GitHub Actions

Deploying AI applications quickly and securely is essential for scaling modern services. This guide walks you through deploying a FastAPI-based AI agent to **Google Cloud Run**, storing Docker images in **Artifact Registry**, and automating the pipeline using **GitHub Actions**.

---

## ✅ Prerequisites

Make sure you have:

* A **Google Cloud Platform (GCP)** project with billing enabled
* Installed tools:

  * [Google Cloud CLI](https://cloud.google.com/sdk/docs/install)
  * [Docker](https://docs.docker.com/get-docker/)
  * [GitHub CLI](https://docs.github.com/en/github-cli/github-cli/quickstart)
* A [GitHub repository](https://github.com/new)
* An [OpenAI API Key](https://platform.openai.com/account/api-keys)
* Permissions to create and manage service accounts and IAM roles in GCP

---

## 🧠 Step 1: Create Your AI Agent (FastAPI)

Create `main.py`:

```python
from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

class Prompt(BaseModel):
    message: str

@app.post("/generate")
async def generate_response(prompt: Prompt):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt.message}]
    )
    return {"reply": response.choices[0].message.content}

# Create a new helath check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok"}
```

Create `requirements.txt`:

```txt
fastapi
uvicorn
pydantic
openai
python-dotenv
```

---

## 📦 Step 2: Dockerize the App

Create a `Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY . /app
RUN pip install -r requirements.txt

EXPOSE ${PORT:-8000}

# Define the command to run the application
# Use 0.0.0.0 to make it accessible from outside the container
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

Build and test locally:

```bash
docker build -t ai-agent .
docker run -p 8080:8080 ai-agent
```

---

## 🔐 Step 3: Set Up IAM Roles and Service Account

```bash
PROJECT_ID="your-project-id"
SA_NAME="cloud-run-deployer"
PROJECT_NUMBER="your-project-number"
```

Create a deployer service account:

```bash
gcloud iam service-accounts create $SA_NAME \
  --description="Deploys to Cloud Run" \
  --display-name="Cloud Run Deployer"
```

Assign necessary roles:

```bash
# Cloud Run Admin
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.admin"

# Artifact Registry Writer
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

# ActAs permission on runtime service account
gcloud iam service-accounts add-iam-policy-binding $PROJECT_NUMBER-compute@developer.gserviceaccount.com \
  --member="serviceAccount:$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"
```

Generate and download a key file:

```bash
gcloud iam service-accounts keys create key.json \
  --iam-account=$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com
```

---

## 🗝️ Step 4: Add Secrets to GitHub

In your GitHub repo, you can either use the GitHub web interface (**Settings → Secrets → Actions**) or the GitHub CLI:

### Option 1: GitHub UI

* `GCP_PROJECT_ID`: your GCP project ID
* `GCP_SA_KEY`: contents of `key.json`
* `OPENAI_API_KEY`: your OpenAI key

### Option 2: GitHub CLI

Make sure you're authenticated with the GitHub CLI (`gh auth login`), then run:

```bash
# Add project ID
gh secret set GCP_PROJECT_ID --body "$PROJECT_ID"

# Add service account key from file
gh secret set GCP_SA_KEY < key.json

# Add OpenAI API key
gh secret set OPENAI_API_KEY --body "your-openai-api-key"
```

---

## ⚙️ Step 5: GitHub Actions Workflow

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches: [main]

env:
  GCP_REGION: us-central1
  GCP_PROJECT_ID: <your-project-id>
  GCP_IMAGE_REPO: ai-agents

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repo
        uses: actions/checkout@v3

      - name: Set up Google Cloud SDK
        uses: google-github-actions/auth@v2
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}

      - name: Configure Docker
        run: gcloud auth configure-docker ${{ env.GCP_REGION }}-docker.pkg.dev

      - name: Build Docker image
        run: |
          docker build -t ${{ env.GCP_REGION }}-docker.pkg.dev/${{ env.GCP_PROJECT_ID }}/${{ env.GCP_IMAGE_REPO }}/ai-agent:latest .
          docker push ${{ env.GCP_REGION }}-docker.pkg.dev/${{ env.GCP_PROJECT_ID }}/${{ env.GCP_IMAGE_REPO }}/ai-agent:latest

      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy ai-agent \
            --image ${{ env.GCP_REGION }}-docker.pkg.dev/${{ env.GCP_PROJECT_ID }}/${{ env.GCP_IMAGE_REPO }}/ai-agent:latest \
            --region ${{ env.GCP_REGION }} \
            --platform managed \
            --allow-unauthenticated \
            --set-env-vars OPENAI_API_KEY=${{ secrets.OPENAI_API_KEY }}

```

---

## 📡 Step 6: Test Your Deployment

Once deployed, you’ll get a Cloud Run URL. Test it using:

```bash
curl -X POST https://YOUR_CLOUD_RUN_URL/generate \
  -H "Content-Type: application/json" \
  -d '{"message": "Tell me a joke"}'
```

> 💡 To test locally, you can also add `OPENAI_API_KEY` to a `.env` file or use `export OPENAI_API_KEY=your-key`.

---

## ✅ Conclusion

You’ve now fully automated the deployment of an AI agent to Google Cloud Run using Docker, Artifact Registry, and GitHub Actions. This pipeline is scalable, secure, and CI/CD ready.

Next: Add CI tests, monitoring, or even LangChain integration to scale up your agent intelligence!
