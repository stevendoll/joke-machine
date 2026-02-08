#!/bin/bash

# Build and deploy Joke Machine as Lambda container

set -e

echo "🐳 Building Lambda container..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first:"
    echo "   brew install --cask docker"
    exit 1
fi

# Check AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is not installed. Please install it first."
    exit 1
fi

# Get AWS account ID and region
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=${AWS_REGION:-us-east-1}
ECR_REGISTRY="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com"

echo "🔧 Using ECR registry: $ECR_REGISTRY"

# Create ECR repository if it doesn't exist
REPO_NAME="joke-machine"
echo "📦 Creating ECR repository: $REPO_NAME"
aws ecr describe-repositories --repository-names $REPO_NAME --region $REGION > /dev/null 2>&1 || \
    aws ecr create-repository --repository-name $REPO_NAME --region $REGION

# Login to ECR
echo "🔐 Logging into ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_REGISTRY

# Build and deploy with SAM (handles container images correctly)
echo "� Building with SAM..."
sam build --use-container

# Deploy with SAM
echo "🚀 Deploying Lambda container..."
sam deploy \
    --stack-name joke-machine-container \
    --capabilities CAPABILITY_IAM \
    --region $REGION \
    --image-repository $ECR_REGISTRY/$REPO_NAME \
    --no-confirm-changeset

# Get API URL
echo "🌐 Getting API URL..."
API_URL=$(aws cloudformation describe-stacks \
    --stack-name joke-machine-container \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
    --output text)

echo "✅ Container deployment complete!"
echo "🔗 API URL: $API_URL"
echo "📖 API Docs: $API_URL/docs"
echo "🏥 Health Check: $API_URL/health"

# Test deployment
echo "🧪 Testing deployment..."
curl -s "$API_URL/health" | jq .

echo "🎉 Joke Machine API is live!"
