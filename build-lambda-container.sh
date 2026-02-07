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

# Build Docker image
echo "🐳 Building Docker image..."
docker build -f Dockerfile.aws -t $REPO_NAME:latest .

# Tag image for ECR
echo "🏷️  Tagging image for ECR..."
docker tag $REPO_NAME:latest $ECR_REGISTRY/$REPO_NAME:latest

# Push to ECR
echo "📤 Pushing to ECR..."
docker push $ECR_REGISTRY/$REPO_NAME:latest

# Update CloudFormation template for container
echo "📋 Creating container template..."
cat > template-container.yaml << EOF
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31
Description: 'Joke Machine API using Lambda Container'

Resources:
  JokeMachineFunction:
    Type: AWS::Serverless::Function
    Properties:
      PackageType: Image
      Architectures:
        - x86_64
      Events:
        Api:
          Type: HttpApi
          Properties:
            Path: /{proxy+}
            Method: ANY
      Policies:
        - CloudWatchLogsFullAccess
      Timeout: 30
      MemorySize: 512
      ImageUri: $ECR_REGISTRY/$REPO_NAME@sha256:3ca55252160504b94cfe022fdee5aa22dbe08c4f187322e627e463e4b1a26a30

Outputs:
  ApiUrl:
    Description: "API Gateway endpoint URL for Prod stage"
    Value: !Sub "https://\${ServerlessHttpApi}.execute-api.\${AWS::Region}.amazonaws.com/"
  FunctionName:
    Description: "Lambda Function Name"
    Value: !Ref JokeMachineFunction
EOF

# Deploy container
echo "🚀 Deploying Lambda container..."
sam deploy \
    --template-file template-container.yaml \
    --stack-name joke-machine-container \
    --capabilities CAPABILITY_IAM \
    --region $REGION \
    --image-repository $ECR_REGISTRY/$REPO_NAME

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
