# AWS Deployment Guide

## 🚀 Deploying Joke Machine API to AWS

### Prerequisites

1. **AWS CLI** - Install and configure
   ```bash
   # Install AWS CLI
   curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
   unzip awscliv2.zip
   sudo ./aws/install
   
   # Configure
   aws configure
   ```

2. **AWS SAM CLI** - Serverless Application Model
   ```bash
   # macOS
   brew install aws-sam-cli
   
   # Verify installation
   sam --version
   ```

3. **S3 Bucket** - For deployment artifacts
   ```bash
   # Create bucket (replace with your account ID)
   aws s3 mb s3://joke-machine-deployment-$(aws sts get-caller-identity --query Account --output text)
   ```

---

## 📦 Quick Deployment

### Option 1: Automated Script
```bash
# Make script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

### Option 2: Manual Steps

#### 1. Build Dependencies
```bash
mkdir -p dependencies/python
pip install -r requirements.txt -t dependencies/python/
```

#### 2. Package Application
```bash
sam package \
    --template-file template.yaml \
    --output-template-file packaged.yaml \
    --s3-bucket joke-machine-deployment-$(aws sts get-caller-identity --query Account --output text)
```

#### 3. Deploy to AWS
```bash
sam deploy \
    --template-file packaged.yaml \
    --stack-name joke-machine-api \
    --capabilities CAPABILITY_IAM \
    --region us-east-1
```

---

## 🔧 Configuration Details

### Lambda Function Settings
- **Runtime**: Python 3.13
- **Memory**: 512 MB
- **Timeout**: 30 seconds
- **Storage**: Ephemeral `/tmp` directory
- **Layers**: Dependencies packaged separately

### API Gateway
- **Type**: HTTP API (faster, cheaper)
- **Routes**: All methods to `/{proxy+}`
- **CORS**: Enabled for all origins

### Database
- **Location**: `/tmp/jokes.db` (Lambda ephemeral)
- **Seeding**: Auto-populated on cold start
- **Persistence**: Not available (serverless limitation)

---

## 🌐 Accessing Deployed API

After deployment, you'll get an API URL like:
```
https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/
```

### Endpoints
- **API Base**: `{API_URL}`
- **Interactive Docs**: `{API_URL}/docs`
- **Health Check**: `{API_URL}/health`
- **Get All Jokes**: `{API_URL}/jokes`
- **Get Random Joke**: `POST {API_URL}/jokes`

---

## 🧪 Testing Deployment

```bash
# Get API URL from CloudFormation
API_URL=$(aws cloudformation describe-stacks \
    --stack-name joke-machine-api \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
    --output text)

# Test health endpoint
curl "$API_URL/health"

# Test jokes endpoint
curl "$API_URL/jokes"

# Test with parameters
curl -X POST "$API_URL/jokes" \
     -H "Content-Type: application/json" \
     -d '{"category": "programming"}'
```

---

## 📊 Monitoring

### CloudWatch Logs
```bash
# View logs
sam logs -n JokeMachineFunction --stack-name joke-machine-api --tail

# Or via AWS CLI
aws logs tail /aws/lambda/joke-machine-api-JokeMachineFunction-xxxxxxxx --follow
```

### Metrics
- **Lambda invocations**
- **Lambda duration**
- **API Gateway requests**
- **Error rates**

---

## 🔄 Updates and Rollbacks

### Update Application
```bash
# Make changes to code
# Re-run deployment
./deploy.sh
```

### Rollback
```bash
# Delete current stack
aws cloudformation delete-stack --stack-name joke-machine-api

# Deploy previous version
sam deploy \
    --template-file previous-packaged.yaml \
    --stack-name joke-machine-api \
    --capabilities CAPABILITY_IAM
```

---

## 🚨 Troubleshooting

### Common Issues

#### 1. Permission Errors
```bash
# Ensure IAM user has:
# - Lambda full access
# - CloudFormation full access
# - S3 full access
# - IAM full access
```

#### 2. Memory Issues
- Increase `MemorySize` in `template.yaml`
- Monitor CloudWatch metrics

#### 3. Timeout Issues
- Increase `Timeout` in `template.yaml`
- Optimize database queries

#### 4. Cold Start Delays
- Enable provisioned concurrency
- Use smaller dependency layers

---

## 💰 Cost Optimization

### Free Tier Benefits
- **Lambda**: 1M requests/month free
- **API Gateway**: 1M API calls/month free
- **CloudWatch**: 10GB logs/month free

### Cost Reduction Tips
- Use HTTP API (cheaper than REST API)
- Optimize Lambda memory usage
- Enable data transfer compression
- Monitor and set up billing alerts

---

## 🔒 Security Considerations

### API Security
- API Gateway handles DDoS protection
- No sensitive data in environment variables
- Input validation via Pydantic models
- Rate limiting can be added via API Gateway

### Database Security
- Database in `/tmp` (isolated per invocation)
- No persistent storage (security feature)
- Input sanitization in all endpoints

---

## 🎉 Production Ready!

Your Joke Machine API is now running on AWS Lambda with:
- ✅ Auto-scaling
- ✅ Pay-per-use pricing
- ✅ High availability
- ✅ Built-in monitoring
- ✅ Global CDN via CloudFront (optional)

For production use, consider:
- Adding CloudFront distribution
- Setting up custom domain
- Implementing API keys/rate limiting
- Adding comprehensive logging
