# CI/CD Deployment Guide - Module 5

## 🎯 Overview

This guide covers setting up GitHub Actions CI/CD pipeline that automatically builds and deploys the Bank Churn API to Azure Container Apps **only on tagged releases** (e.g., v1.0.0, v1.0.1).

---

## 📋 Prerequisites

Before setting up CI/CD, ensure you have:

1. ✅ Azure Container Registry (ACR) created
2. ✅ Azure Container App deployed and running
3. ✅ GitHub repository initialized with code pushed
4. ✅ Azure CLI installed and logged in

---

## 🔐 Step 1: Create Azure Service Principal

The GitHub Actions workflow needs permissions to deploy to Azure. Create a Service Principal with the required permissions:

### Option A: With `jq` (Recommended)

```bash
# Install jq if not already installed
sudo apt install jq

# Set variables
RESOURCE_GROUP="rg-mlops-bank-churn"
SUBSCRIPTION_ID=$(az account show --query id -o tsv | tr -d '\r')

# Create Service Principal and format for GitHub
SP_JSON=$(az ad sp create-for-rbac \
  --name "github-actions-$(date +%s)" \
  --role contributor \
  --scopes "/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP}" \
  --output json)

# Extract and format the 4 required fields
echo $SP_JSON | jq -c '{clientId: .appId, clientSecret: .password, subscriptionId: "'"$SUBSCRIPTION_ID"'", tenantId: .tenant}'
```

This will output a single-line JSON like:
```json
{"clientId":"xxxxxxxx-xxxx-...","clientSecret":"your_password","subscriptionId":"xxxx-...","tenantId":"xxxx-..."}
```

**Copy this entire JSON output** - you'll need it for GitHub Secrets.

### Option B: Without `jq`

```bash
RESOURCE_GROUP="rg-mlops-bank-churn"
SUBSCRIPTION_ID=$(az account show --query id -o tsv | tr -d '\r')

# Create Service Principal
az ad sp create-for-rbac \
  --name "github-actions-$(date +%s)" \
  --role contributor \
  --scopes "/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP}" \
  --output json > sp_output.json

# Manually format the JSON with these 4 fields:
# - clientId (from appId)
# - clientSecret (from password)
# - subscriptionId (from your subscription)
# - tenantId (from tenant)
```

---

## 🔑 Step 2: Configure GitHub Secrets

Go to your GitHub repository → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Add the following secrets:

### 1. `AZURE_CREDENTIALS`
Paste the entire JSON from Step 1:
```json
{"clientId":"xxx","clientSecret":"xxx","subscriptionId":"xxx","tenantId":"xxx"}
```

### 2. `ACR_LOGIN_SERVER`
Your Azure Container Registry login server (e.g., `acrmlopsbank.azurecr.io`)

```bash
# Get it from Azure
az acr show --name <your-acr-name> --query loginServer -o tsv
```

### 3. `ACR_USERNAME`
Your ACR username (usually the ACR name)

```bash
# Get it from Azure
az acr credential show --name <your-acr-name> --query username -o tsv
```

### 4. `ACR_PASSWORD`
Your ACR password

```bash
# Get it from Azure
az acr credential show --name <your-acr-name> --query passwords[0].value -o tsv
```

### 5. `RESOURCE_GROUP`
Your Azure resource group name (e.g., `rg-mlops-bank-churn`)

```
rg-mlops-bank-churn
```

---

## 📝 Step 3: Update Workflow Configuration (if needed)

The workflow file is already created at `.github/workflows/deploy.yml`. Review and update these values if your naming is different:

```yaml
env:
  IMAGE_NAME: bank-churn-api          # Docker image name
  CONTAINER_APP_NAME: bank-churn-api  # Azure Container App name
  PYTHON_VERSION: '3.11'              # Python version
```

---

## 🚀 Step 4: Commit and Push Changes

```bash
# Add all new files
git add .github/workflows/deploy.yml
git add tests/test_partner_api.py
git add .env.example
git add .gitignore

# Commit
git commit -m "feat: add CI/CD pipeline with GitHub Actions"

# Push to main
git push origin main
```

**Note:** This push will NOT trigger the workflow because it only runs on tags.

---

## 🏷️ Step 5: Create and Push a Release Tag

The workflow triggers **only on tagged releases** (v*.*.*). Create your first release:

```bash
# Create a tag for version 1.0.0
git tag -a v1.0.0 -m "Release version 1.0.0 - Initial production deployment"

# Push the tag to GitHub
git push origin v1.0.0
```

This will automatically trigger the CI/CD pipeline!

---

## 📊 Step 6: Monitor the Deployment

### Watch GitHub Actions

1. Go to your GitHub repository
2. Click on **Actions** tab
3. You should see the workflow "CI/CD - Build and Deploy to Azure" running
4. Click on it to see detailed logs

The workflow has 3 jobs:
- **test**: Runs pytest with coverage
- **build-and-push**: Builds and pushes Docker image to ACR
- **deploy**: Deploys to Azure Container Apps and runs health checks

### Check Azure Portal

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to your **Container App** → **Log stream**
3. Watch real-time logs as the new version deploys

---

## 🧪 Step 7: Test the Deployment

Once the workflow completes (usually 5-10 minutes), test your API:

```bash
# Get your Container App URL
FQDN=$(az containerapp show \
  --name bank-churn-api \
  --resource-group rg-mlops-bank-churn \
  --query properties.configuration.ingress.fqdn \
  --output tsv | tr -d '\r')

API_URL="https://$FQDN"

# Test health endpoint
curl $API_URL/health | jq '.'

# Test prediction
curl -X POST "$API_URL/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "CreditScore": 650,
    "Age": 35,
    "Tenure": 5,
    "Balance": 80000.0,
    "NumOfProducts": 2,
    "HasCrCard": 1,
    "IsActiveMember": 1,
    "EstimatedSalary": 75000.0,
    "Geography_Germany": 0,
    "Geography_Spain": 0
  }' | jq '.'
```

---

## 🔄 Step 8: Future Deployments

For subsequent deployments, simply create a new tag:

```bash
# Make your changes and commit
git add .
git commit -m "feat: add new feature"
git push origin main

# Create new version tag
git tag -a v1.0.1 -m "Release version 1.0.1 - Bug fixes"
git push origin v1.0.1
```

The CI/CD pipeline will automatically:
1. Run tests
2. Build new Docker image with version tag
3. Push to Azure Container Registry
4. Deploy to Azure Container Apps
5. Run health checks
6. Post deployment summary as a commit comment

---

## 🎓 Exercise 2: Test Partner API

### Share Your API URL

Share your API URL with a classmate:
```bash
echo "https://$FQDN"
```

### Test Partner's API

When you receive a partner's API URL, test it:

```bash
# Run the test script with partner's URL
python tests/test_partner_api.py https://partner-api-url.azurecontainerapps.io
```

This script will:
1. ✅ Check health endpoint
2. ✅ Make 10 predictions with random customer data
3. ✅ Compare results with your local model
4. ✅ Save detailed results to `resultat.txt`
5. ✅ Show agreement statistics

### Observe Logs in Azure Portal

While testing:
1. Go to Azure Portal → Your Container App
2. Click **Monitoring** → **Log stream**
3. Watch incoming requests in real-time
4. See prediction logs and response times

You can also view logs with Azure CLI:
```bash
az containerapp logs show \
  --name bank-churn-api \
  --resource-group rg-mlops-bank-churn \
  --follow
```

---

## 📈 Monitoring and Debugging

### View Deployment History

```bash
# List recent revisions
az containerapp revision list \
  --name bank-churn-api \
  --resource-group rg-mlops-bank-churn \
  --query "[].{Name:name, CreatedTime:properties.createdTime, Active:properties.active}" \
  --output table
```

### Rollback to Previous Version

If something goes wrong:

```bash
# List revisions
az containerapp revision list \
  --name bank-churn-api \
  --resource-group rg-mlops-bank-churn \
  --output table

# Activate previous revision
az containerapp revision activate \
  --name bank-churn-api \
  --resource-group rg-mlops-bank-churn \
  --revision <previous-revision-name>
```

### Check Container Logs

```bash
# Real-time logs
az containerapp logs show \
  --name bank-churn-api \
  --resource-group rg-mlops-bank-churn \
  --follow

# Last 100 lines
az containerapp logs show \
  --name bank-churn-api \
  --resource-group rg-mlops-bank-churn \
  --tail 100
```

---

## ✅ Checkpoint - Module 5

Before moving to the next module, verify:

- ✅ GitHub Actions workflow file created (`.github/workflows/deploy.yml`)
- ✅ All GitHub Secrets configured (5 secrets)
- ✅ Service Principal has correct permissions
- ✅ First tag (v1.0.0) created and pushed
- ✅ Workflow completed successfully in GitHub Actions
- ✅ Application accessible via HTTPS
- ✅ Health check returns 200 OK
- ✅ Prediction endpoint works
- ✅ Tested partner's API with test script
- ✅ Observed logs in Azure Portal

---

## 🐛 Troubleshooting

### Workflow fails on "Login to Azure"

**Problem:** Invalid Azure credentials
**Solution:** 
1. Verify `AZURE_CREDENTIALS` secret has all 4 fields
2. Recreate Service Principal with correct scope
3. Ensure no extra whitespace in the JSON

### Workflow fails on "Push Docker image"

**Problem:** ACR authentication failed
**Solution:**
1. Verify ACR credentials are correct
2. Enable admin user in ACR: `az acr update --name <acr-name> --admin-enabled true`
3. Regenerate ACR password if needed

### Container App fails health check

**Problem:** Application not starting or model not found
**Solution:**
1. Check logs: `az containerapp logs show --name bank-churn-api --resource-group rg-mlops-bank-churn --follow`
2. Verify model file exists in Docker image
3. Check `MODEL_PATH` environment variable

### Test script fails to connect

**Problem:** Partner's API unreachable
**Solution:**
1. Verify URL is correct (include https://)
2. Check if Container App is running in Azure Portal
3. Test with browser: `https://your-api-url/docs`

---

## 📚 Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Azure Container Apps Documentation](https://learn.microsoft.com/en-us/azure/container-apps/)
- [Azure CLI Reference](https://learn.microsoft.com/en-us/cli/azure/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)

---

## 🎯 Key Concepts Learned

1. **Tag-based deployments**: Production deployments only on version tags
2. **Multi-stage pipeline**: Test → Build → Deploy
3. **Azure authentication**: Service Principal with minimal permissions
4. **Container orchestration**: ACR + Container Apps
5. **Health checks**: Automated testing after deployment
6. **Version tracking**: Git tags linked to Docker image tags
7. **Rollback strategy**: Activate previous revisions if needed
8. **Monitoring**: Real-time logs and metrics in Azure Portal

---

**Congratulations! 🎉** Your CI/CD pipeline is now fully operational. Every time you push a new version tag, your application will automatically build, test, and deploy to production!
