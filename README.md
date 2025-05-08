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
import os
import openai

app = FastAPI()

class Prompt(BaseModel):
    message: str

@app.post("/generate")
async def generate_response(prompt: Prompt):
    openai.api_key = os.getenv("OPENAI_API_KEY")
    client = openai.OpenAI()
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt.message}]
    )
    return {"reply": response.choices[0].message.content}
```

Create `requirements.txt`:

```txt
fastapi
uvicorn
openai>=1.0.0
pydantic
```

---

## 📦 Step 2: Dockerize the App

Create a `Dockerfile`:

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY . /app
RUN pip install -r requirements.txt
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
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
RUNTIME_SA="YOUR_PROJECT_NUMBER-compute@developer.gserviceaccount.com"
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
gcloud iam service-accounts add-iam-policy-binding $RUNTIME_SA \
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

jobs:
  deploy:
    runs-on: ubuntu-latest
    env:
      REGION: us-central1
      REPO_NAME: ai-agent
      IMAGE_NAME: ai-agent
      IMAGE_URI: us-central1-docker.pkg.dev/${{ secrets.GCP_PROJECT_ID }}/ai-agent/ai-agent

    steps:
      - name: Checkout repository
        uses: actions/checkout@v3

      - name: Set up Google Cloud SDK
        uses: google-github-actions/setup-gcloud@v1
        with:
          project_id: ${{ secrets.GCP_PROJECT_ID }}
          service_account_key: ${{ secrets.GCP_SA_KEY }}

      - name: Enable Artifact Registry API
        run: gcloud services enable artifactregistry.googleapis.com

      - name: Ensure Artifact Registry Repo Exists
        run: |
          gcloud artifacts repositories describe $REPO_NAME \
            --location=$REGION || \
          gcloud artifacts repositories create $REPO_NAME \
            --repository-format=docker \
            --location=$REGION \
            --description="Docker repo for AI agent"

      - name: Authenticate Docker
        run: gcloud auth configure-docker $REGION-docker.pkg.dev

      - name: Build and Push Image
        run: |
          docker build -t $IMAGE_URI .
          docker push $IMAGE_URI

      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy $IMAGE_NAME \
            --image $IMAGE_URI \
            --region $REGION \
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
