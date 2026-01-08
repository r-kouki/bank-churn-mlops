#!/bin/bash

# Quick Commands Reference for Module 5 & Exercise 2
# This file contains helpful commands - DO NOT execute this script directly

echo "================================================================"
echo "MODULE 5: CI/CD WITH GITHUB ACTIONS - QUICK REFERENCE"
echo "================================================================"

# ============================================
# STEP 1: CREATE AZURE SERVICE PRINCIPAL
# ============================================
echo ""
echo "1️⃣  Create Azure Service Principal for GitHub Actions:"
echo "-------------------------------------------------------"
cat << 'CMD'
RESOURCE_GROUP="rg-mlops-bank-churn"
SUBSCRIPTION_ID=$(az account show --query id -o tsv | tr -d '\r')

SP_JSON=$(az ad sp create-for-rbac \
  --name "github-actions-$(date +%s)" \
  --role contributor \
  --scopes "/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP}" \
  --output json)

echo $SP_JSON | jq -c '{clientId: .appId, clientSecret: .password, subscriptionId: "'"$SUBSCRIPTION_ID"'", tenantId: .tenant}'
CMD

# ============================================
# STEP 2: GET ACR CREDENTIALS
# ============================================
echo ""
echo "2️⃣  Get Azure Container Registry Credentials:"
echo "-------------------------------------------------------"
cat << 'CMD'
# Replace <your-acr-name> with your ACR name
ACR_NAME="acrmlopsbank"  # Change this!

# Login server
az acr show --name $ACR_NAME --query loginServer -o tsv

# Username
az acr credential show --name $ACR_NAME --query username -o tsv

# Password
az acr credential show --name $ACR_NAME --query passwords[0].value -o tsv
CMD

# ============================================
# STEP 3: CONFIGURE GITHUB SECRETS
# ============================================
echo ""
echo "3️⃣  Configure GitHub Secrets (in GitHub UI):"
echo "-------------------------------------------------------"
echo "Go to: GitHub Repo → Settings → Secrets and variables → Actions"
echo ""
echo "Add these 5 secrets:"
echo "  • AZURE_CREDENTIALS        → JSON from step 1"
echo "  • ACR_LOGIN_SERVER         → e.g., acrmlopsbank.azurecr.io"
echo "  • ACR_USERNAME             → ACR username"
echo "  • ACR_PASSWORD             → ACR password"
echo "  • RESOURCE_GROUP           → rg-mlops-bank-churn"

# ============================================
# STEP 4: COMMIT AND PUSH
# ============================================
echo ""
echo "4️⃣  Commit and Push Changes:"
echo "-------------------------------------------------------"
cat << 'CMD'
git add .github/workflows/deploy.yml
git add tests/test_partner_api.py
git add .env.example
git add .gitignore
git add CICD_DEPLOYMENT_GUIDE.md

git commit -m "feat: add CI/CD pipeline with GitHub Actions

- Add GitHub Actions workflow triggered on version tags
- Add partner API testing script for Exercise 2
- Add environment variable documentation
- Update .gitignore for deployment artifacts
- Add comprehensive deployment guide"

git push origin main
CMD

# ============================================
# STEP 5: CREATE RELEASE TAG
# ============================================
echo ""
echo "5️⃣  Create and Push Release Tag (triggers CI/CD):"
echo "-------------------------------------------------------"
cat << 'CMD'
# Create version tag
git tag -a v1.0.0 -m "Release version 1.0.0 - Initial production deployment"

# Push tag (this triggers the workflow!)
git push origin v1.0.0
CMD

# ============================================
# STEP 6: MONITOR DEPLOYMENT
# ============================================
echo ""
echo "6️⃣  Monitor Deployment:"
echo "-------------------------------------------------------"
echo "• GitHub: https://github.com/YOUR-USERNAME/bank-churn-mlops/actions"
echo "• Azure Portal: Container Apps → bank-churn-api → Log stream"
echo ""
cat << 'CMD'
# Watch logs in terminal
az containerapp logs show \
  --name bank-churn-api \
  --resource-group rg-mlops-bank-churn \
  --follow
CMD

# ============================================
# STEP 7: TEST DEPLOYMENT
# ============================================
echo ""
echo "7️⃣  Test Deployment:"
echo "-------------------------------------------------------"
cat << 'CMD'
# Get API URL
FQDN=$(az containerapp show \
  --name bank-churn-api \
  --resource-group rg-mlops-bank-churn \
  --query properties.configuration.ingress.fqdn \
  --output tsv | tr -d '\r')
API_URL="https://$FQDN"

echo "API URL: $API_URL"

# Test health
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
CMD

# ============================================
# EXERCISE 2: TEST PARTNER API
# ============================================
echo ""
echo "================================================================"
echo "EXERCISE 2: TEST PARTNER API"
echo "================================================================"

echo ""
echo "8️⃣  Share Your API URL with Partner:"
echo "-------------------------------------------------------"
cat << 'CMD'
# Get your API URL
FQDN=$(az containerapp show \
  --name bank-churn-api \
  --resource-group rg-mlops-bank-churn \
  --query properties.configuration.ingress.fqdn \
  --output tsv | tr -d '\r')

echo "Share this URL: https://$FQDN"
CMD

echo ""
echo "9️⃣  Test Partner's API:"
echo "-------------------------------------------------------"
cat << 'CMD'
# When you receive partner's URL, test it:
python tests/test_partner_api.py https://partner-api-url.azurecontainerapps.io

# Results will be saved to resultat.txt
cat resultat.txt
CMD

echo ""
echo "🔟 Observe Logs in Azure Portal:"
echo "-------------------------------------------------------"
echo "1. Go to Azure Portal"
echo "2. Navigate to: Container Apps → bank-churn-api"
echo "3. Click: Monitoring → Log stream"
echo "4. Watch requests in real-time as partner tests your API"

# ============================================
# FUTURE DEPLOYMENTS
# ============================================
echo ""
echo "================================================================"
echo "FUTURE DEPLOYMENTS"
echo "================================================================"
echo ""
cat << 'CMD'
# Make changes, commit, and push
git add .
git commit -m "feat: your changes"
git push origin main

# Create new version tag to trigger deployment
git tag -a v1.0.1 -m "Release version 1.0.1"
git push origin v1.0.1
CMD

echo ""
echo "================================================================"
echo "✅ Setup complete! Follow the steps above to deploy."
echo "📖 For detailed instructions, see: CICD_DEPLOYMENT_GUIDE.md"
echo "================================================================"
