#!/bin/bash

# AWS Deployment Script for Joke Machine API

set -e

echo "🚀 Starting AWS deployment..."

# Check AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is not installed. Please install it first."
    exit 1
fi

# Check SAM CLI is installed
if ! command -v sam &> /dev/null; then
    echo "❌ AWS SAM CLI is not installed. Please install it first."
    echo "📖 Installation guide: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html"
    exit 1
fi

# Build dependencies for Lambda layer
echo "📦 Building dependencies..."
mkdir -p dependencies/python
pip3 install -r requirements.txt -t dependencies/python/

# Package the application
echo "📋 Packaging application..."
sam package \
    --template-file template.yaml \
    --output-template-file packaged.yaml \
    --s3-bucket joke-machine-deployment-$(aws sts get-caller-identity --query Account --output text)

# Deploy the application
echo "🚀 Deploying to AWS..."
sam deploy \
    --template-file packaged.yaml \
    --stack-name joke-machine-api \
    --capabilities CAPABILITY_IAM \
    --region us-east-1

# Get API URL
echo "🌐 Getting API URL..."
API_URL=$(aws cloudformation describe-stacks \
    --stack-name joke-machine-api \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
    --output text)

echo "✅ Deployment complete!"
echo "🔗 API URL: $API_URL"
echo "📖 API Docs: $API_URL/docs"
echo "🏥 Health Check: $API_URL/health"

# Test deployment
echo "🧪 Testing deployment..."
curl -s "$API_URL/health" | jq .

echo "🎉 Joke Machine API is live!"
