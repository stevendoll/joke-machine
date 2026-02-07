#!/bin/bash

# Automated AWS Lambda Deployment Script for Joke Machine
set -e

AWS_REGION="us-east-1"
FUNCTION_NAME="joke-machine"
ECR_REPO_NAME="joke-machine"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_URI="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_NAME}"

echo "🚀 Starting AWS Lambda deployment for Joke Machine..."

# Step 1: Build Docker image
echo "📦 Building Docker image..."
docker build -f Dockerfile.aws -t ${FUNCTION_NAME}-lambda .

# Step 2: Login to ECR
echo "🔐 Logging into ECR..."
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_URI}

# Step 3: Tag and push image
echo "📤 Pushing image to ECR..."
docker tag ${FUNCTION_NAME}-lambda:latest ${ECR_URI}:latest
docker push ${ECR_URI}:latest

# Step 4: Create/Update IAM role
echo "👤 Creating/updating IAM role..."
if ! aws iam get-role --role-name ${FUNCTION_NAME}-lambda-role --region ${AWS_REGION} >/dev/null 2>&1; then
    echo "Creating new IAM role..."
    aws iam create-role --role-name ${FUNCTION_NAME}-lambda-role \
        --assume-role-policy-document '{
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {"Service": "lambda.amazonaws.com"},
                "Action": "sts:AssumeRole"
            }]
        }' --region ${AWS_REGION}
    
    aws iam attach-role-policy --role-name ${FUNCTION_NAME}-lambda-role \
        --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole \
        --region ${AWS_REGION}
    
    echo "Waiting for role to be available..."
    sleep 10
fi

ROLE_ARN=$(aws iam get-role --role-name ${FUNCTION_NAME}-lambda-role --query Role.Arn --output text --region ${AWS_REGION})

# Step 5: Create/Update ECR repository
echo "📋 Creating/updating ECR repository..."
if ! aws ecr describe-repositories --repository-names ${ECR_REPO_NAME} --region ${AWS_REGION} >/dev/null 2>&1; then
    aws ecr create-repository --repository-name ${ECR_REPO_NAME} --region ${AWS_REGION}
fi

# Step 6: Create/Update Lambda function
echo "⚡ Creating/updating Lambda function..."
if aws lambda get-function --function-name ${FUNCTION_NAME} --region ${AWS_REGION} >/dev/null 2>&1; then
    echo "Updating existing Lambda function..."
    aws lambda update-function-code \
        --function-name ${FUNCTION_NAME} \
        --image-uri ${ECR_URI}:latest \
        --region ${AWS_REGION}
else
    echo "Creating new Lambda function..."
    aws lambda create-function \
        --function-name ${FUNCTION_NAME} \
        --package-type Image \
        --code ImageUri=${ECR_URI}:latest \
        --role ${ROLE_ARN} \
        --region ${AWS_REGION} \
        --timeout 30 \
        --memory-size 256
fi

# Step 7: Create API Gateway
echo "🌐 Creating API Gateway..."
if ! aws apigateway get-rest-apis --query "items[?name=='${FUNCTION_NAME}-api']" --region ${AWS_REGION} | grep -q "${FUNCTION_NAME}-api"; then
    echo "Creating new API Gateway..."
    API_ID=$(aws apigateway create-rest-api --name "${FUNCTION_NAME}-api" --region ${AWS_REGION} --query id --output text)
    
    # Get root resource
    ROOT_ID=$(aws apigateway get-resources --rest-api-id ${API_ID} --region ${AWS_REGION} --query "items[?path=='/'].id" --output text)
    
    # Create proxy resource
    RESOURCE_ID=$(aws apigateway create-resource --rest-api-id ${API_ID} --parent-id ${ROOT_ID} --path-part "{proxy+}" --region ${AWS_REGION} --query id --output text)
    
    # Add POST method
    aws apigateway put-method --rest-api-id ${API_ID} --resource-id ${RESOURCE_ID} --http-method ANY --authorization-type "NONE" --region ${AWS_REGION}
    
    # Add Lambda integration
    aws apigateway put-integration \
        --rest-api-id ${API_ID} \
        --resource-id ${RESOURCE_ID} \
        --http-method ANY \
        --type AWS_PROXY \
        --integration-http-method POST \
        --uri "arn:aws:apigateway:${AWS_REGION}:lambda:path/2015-03-31/functions/arn:aws:lambda:${AWS_REGION}:${ACCOUNT_ID}:function:${FUNCTION_NAME}/invocations" \
        --region ${AWS_REGION}
    
    # Add deployment
    aws apigateway create-deployment --rest-api-id ${API_ID} --stage-name prod --region ${AWS_REGION}
    
    # Add permission for API Gateway to invoke Lambda
    aws lambda add-permission \
        --function-name ${FUNCTION_NAME} \
        --statement-id apigateway-${API_ID} \
        --action lambda:InvokeFunction \
        --principal apigateway.amazonaws.com \
        --source-arn "arn:aws:execute-api:${AWS_REGION}:${ACCOUNT_ID}:${API_ID}/*/*/*" \
        --region ${AWS_REGION}
    
    API_URL="https://${API_ID}.execute-api.${AWS_REGION}.amazonaws.com/prod"
else
    API_ID=$(aws apigateway get-rest-apis --query "items[?name=='${FUNCTION_NAME}-api'].id" --output text --region ${AWS_REGION})
    API_URL="https://${API_ID}.execute-api.${AWS_REGION}.amazonaws.com/prod"
fi

# Step 8: Test deployment
echo "🧪 Testing deployment..."
sleep 5
curl -s "${API_URL}/health" | jq .

echo "✅ Deployment complete!"
echo "🌍 API URL: ${API_URL}"
echo "📊 Health check: ${API_URL}/health"
echo "🎬 Jokes endpoint: ${API_URL}/jokes"
