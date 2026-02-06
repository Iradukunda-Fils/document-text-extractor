# Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying DocuExtract Pro across various platforms, from local development to production cloud environments.

---

## Local Development

### Prerequisites

- Python 3.11+
- Tesseract OCR 4.1+
- Poppler utilities
- 4 GB RAM minimum (8 GB recommended)

### Quick Setup

```bash
# Clone repository
git clone https://github.com/iradukunda-fils/document-text-extractor.git
cd document-text-extractor

# Run automated setup
./setup.sh

# Start Streamlit app
streamlit run app.py
```

### Manual Setup

```bash
# Install system dependencies (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-fra \
    tesseract-ocr-ara \
    poppler-utils

# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Install package in development mode
pip install -e .
```

---

## Docker Deployment

### Build Image

```bash
docker build -t docuextract-pro:latest .
```

### Run Container

```bash
docker run -d \
    --name docuextract \
    -p 8501:8501 \
    -e STREAMLIT_SERVER_MAX_UPLOAD_SIZE=200 \
    -v $(pwd)/uploads:/app/uploads \
    docuextract-pro:latest
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8501:8501"
    environment:
      - STREAMLIT_SERVER_MAX_UPLOAD_SIZE=200
      - STREAMLIT_SERVER_ENABLE_CORS=false
    volumes:
      - ./uploads:/app/uploads
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
```

**Start:**
```bash
docker-compose up -d
```

---

## Streamlit Cloud Deployment

### One-Click Deploy

[![Deploy to Streamlit Cloud](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io)

### Manual Deployment

1. Fork the repository to your GitHub account
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click "New app"
4. Select your forked repository
5. Set main file path: `app.py`
6. Click "Deploy"

### Configuration

Create `.streamlit/config.toml`:

```toml
[server]
maxUploadSize = 200
enableCORS = false
enableXsrfProtection = true

[browser]
gatherUsageStats = false
```

Create `packages.txt`:
```
tesseract-ocr
tesseract-ocr-eng
tesseract-ocr-fra
poppler-utils
```

---

## AWS Deployment

### Option 1: AWS App Runner (Easiest)

```bash
# Install AWS CLI
pip install awscli

# Build and push to ECR
aws ecr create-repository --repository-name docuextract-pro
$(aws ecr get-login --no-include-email --region us-east-1)

docker tag docuextract-pro:latest \
    123456789.dkr.ecr.us-east-1.amazonaws.com/docuextract-pro:latest
    
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/docuextract-pro:latest

# Deploy to App Runner (via Console or CLI)
aws apprunner create-service \
    --service-name docuextract-pro \
    --source-configuration ImageRepository={...}
```

**Recommended Instance**: 1 vCPU, 2 GB RAM ($0.007/hour)

### Option 2: AWS ECS Fargate

```json
// task-definition.json
{
  "family": "docuextract-pro",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "2048",
  "containerDefinitions": [{
    "name": "app",
    "image": "123456789.dkr.ecr.us-east-1.amazonaws.com/docuextract-pro:latest",
    "portMappings": [{
      "containerPort": 8501,
      "protocol": "tcp"
    }],
    "environment": [
      {"name": "STREAMLIT_SERVER_PORT", "value": "8501"}
    ]
  }]
}
```

**Deploy:**
```bash
aws ecs create-cluster --cluster-name docuextract-cluster
aws ecs register-task-definition --cli-input-json file://task-definition.json
aws ecs create-service \
    --cluster docuextract-cluster \
    --service-name docuextract-service \
    --task-definition docuextract-pro \
    --desired-count 2 \
    --launch-type FARGATE
```

### Option 3: AWS EC2

```bash
# Launch t3.medium instance (Ubuntu 22.04)
# Security group: Allow port 8501

ssh ubuntu@<instance-ip>

# Install dependencies
sudo apt-get update
sudo apt-get install -y python3.11 python3-pip tesseract-ocr poppler-utils

# Clone and setup
git clone https://github.com/iradukunda-fils/document-text-extractor.git
cd document-text-extractor
./setup.sh

# Run with systemd
sudo nano /etc/systemd/system/docuextract.service
```

```ini
[Unit]
Description=DocuExtract Pro
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/pdf-text-data-extractor
ExecStart=/home/ubuntu/pdf-text-data-extractor/.venv/bin/streamlit run app.py --server.port=8501
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable docuextract
sudo systemctl start docuextract
```

---

## Google Cloud Platform

### Cloud Run (Recommended)

```bash
# Build and push to GCR
gcloud builds submit --tag gcr.io/PROJECT_ID/docuextract-pro

# Deploy to Cloud Run
gcloud run deploy docuextract-pro \
    --image gcr.io/PROJECT_ID/docuextract-pro \
    --platform managed \
    --region us-central1 \
    --memory 2Gi \
    --cpu 1 \
    --port 8501 \
    --allow-unauthenticated
```

**Auto-scaling**: 0-10 instances (scales to zero when idle)

### GKE (Kubernetes)

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: docuextract-pro
spec:
  replicas: 3
  selector:
    matchLabels:
      app: docuextract
  template:
    metadata:
      labels:
        app: docuextract
    spec:
      containers:
      - name: app
        image: gcr.io/PROJECT_ID/docuextract-pro
        ports:
        - containerPort: 8501
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
---
apiVersion: v1
kind: Service
metadata:
  name: docuextract-service
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 8501
  selector:
    app: docuextract
```

```bash
kubectl apply -f deployment.yaml
```

---

## Azure Deployment

### Azure Container Instances

```bash
az container create \
    --resource-group docuextract-rg \
    --name docuextract-pro \
    --image YOUR_REGISTRY/docuextract-pro:latest \
    --cpu 1 \
    --memory 2 \
    --ports 8501 \
    --dns-name-label docuextract \
    --environment-variables 'STREAMLIT_SERVER_PORT'='8501'
```

### Azure App Service

```bash
# Create App Service Plan
az appservice plan create \
    --name docuextract-plan \
    --resource-group docuextract-rg \
    --sku B1 \
    --is-linux

# Create Web App
az webapp create \
    --resource-group docuextract-rg \
    --plan docuextract-plan \
    --name docuextract-pro \
    --deployment-container-image-name YOUR_REGISTRY/docuextract-pro:latest
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `STREAMLIT_SERVER_PORT` | `8501` | Server port |
| `STREAMLIT_SERVER_MAX_UPLOAD_SIZE` | `200` | Max file size (MB) |
| `TESSDATA_PREFIX` | `/usr/share/tesseract-ocr/4.00/tessdata` | Tesseract data directory |
| `OMP_THREAD_LIMIT` | `4` | OpenMP thread limit for OCR |

---

## Performance Tuning

### Production Settings

```toml
# .streamlit/config.toml
[server]
port = 8501
headless = true
runOnSave = false
maxUploadSize = 200
enableCORS = false
enableXsrfProtection = true

[browser]
gatherUsageStats = false

[runner]
magicEnabled = false
```

### Memory Optimization

```python
# app.py
import streamlit as st

# Limit cache size
@st.cache_data(max_entries=100, ttl=3600)
def _get_pdf_images(file_bytes, dpi=100):
    ...
```

### Load Balancing (NGINX)

```nginx
upstream streamlit {
    server 127.0.0.1:8501;
    server 127.0.0.1:8502;
    server 127.0.0.1:8503;
}

server {
    listen 80;
    server_name docuextract.example.com;

    location / {
        proxy_pass http://streamlit;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

---

## Monitoring & Logging

### Prometheus Metrics

```python
# Add to app.py
from prometheus_client import Counter, Histogram, start_http_server

extraction_count = Counter('extraction_total', 'Total extractions')
extraction_duration = Histogram('extraction_duration_seconds', 'Extraction duration')

@extraction_duration.time()
def extract_with_metrics(file):
    result = extractor.extract(file)
    extraction_count.inc()
    return result

# Start metrics server
start_http_server(9090)
```

### CloudWatch Logs (AWS)

```bash
# Install CloudWatch agent
sudo apt-get install amazon-cloudwatch-agent

# Configure log streaming
cat > /opt/aws/amazon-cloudwatch-agent/etc/config.json <<EOF
{
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [{
          "file_path": "/var/log/docuextract.log",
          "log_group_name": "/aws/docuextract/app",
          "log_stream_name": "{instance_id}"
        }]
      }
    }
  }
}
EOF

sudo systemctl start amazon-cloudwatch-agent
```

---

## Security Hardening

### SSL/TLS Configuration

```bash
# Generate certificates (Let's Encrypt)
sudo certbot --nginx -d docuextract.example.com

# Auto-renewal
sudo systemctl enable certbot.timer
```

### Firewall Rules

```bash
# Allow only HTTP/HTTPS and SSH
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### Rate Limiting (NGINX)

```nginx
limit_req_zone $binary_remote_addr zone=extraction:10m rate=10r/m;

location /extract {
    limit_req zone=extraction burst=5;
    proxy_pass http://streamlit;
}
```

---

## Troubleshooting

### Common Issues

**Port Already in Use**
```bash
# Find process using port 8501
lsof -i :8501

# Kill process
kill -9 <PID>
```

**Tesseract Not Found**
```bash
# Verify installation
which tesseract
tesseract --version

# Add to PATH
export PATH="/usr/bin:$PATH"
```

**Docker Build Fails**
```bash
# Clear build cache
docker builder prune -a

# Build with no cache
docker build --no-cache -t docuextract-pro .
```

---

## Health Checks

### HTTP Endpoint

```python
# Add to app.py
@st.cache_data
def health_check():
    return {"status": "healthy", "timestamp": time.time()}

if st.query_params.get("health"):
    st.json(health_check())
    st.stop()
```

**Usage:**
```bash
curl http://localhost:8501?health=true
```

### Kubernetes Liveness Probe

```yaml
livenessProbe:
  httpGet:
    path: /?health=true
    port: 8501
  initialDelaySeconds: 30
  periodSeconds: 10
```

---

## Backup & Disaster Recovery

### Database-Free Architecture
- No persistent state → no database backups needed
- Configuration stored in Git → version controlled

### Docker Image Backups

```bash
# Tag and push to backup registry
docker tag docuextract-pro:latest backup-registry/docuextract-pro:v2.1.0
docker push backup-registry/docuextract-pro:v2.1.0
```

---

## Cost Estimation

| Platform | Configuration | Monthly Cost | Use Case |
|----------|--------------|---------------|----------|
| **Streamlit Cloud** | Free tier | $0 | Development/demo |
| **AWS EC2 t3.micro** | 1 vCPU, 1GB RAM | $7.50 | Low traffic |
| **AWS Fargate** | 0.5 vCPU, 2GB RAM | $30 | Production (auto-scale) |
| **GCP Cloud Run** | 1 vCPU, 2GB RAM | $15-40 | Variable load |
| **Azure Container Instances** | 1 vCPU, 2GB RAM | $35 | Burst workloads |

**Recommendation**: Start with Streamlit Cloud (free), scale to Cloud Run for production (best cost/performance).

---

## Support

- **Documentation**: [ARCHITECTURE.md](./ARCHITECTURE.md), [API.md](./API.md)
- **Issues**: [GitHub Issues](https://github.com/iradukunda-fils/document-text-extractor/issues)
- **Newsletter**: [Engineering Insights](https://iradukundafils.substack.com/)
