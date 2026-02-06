import json
import os
from main import app
from mangum import Mangum

# Set environment for Lambda deployment
os.environ['AWS_LAMBDA_FUNCTION_NAME'] = 'joke-machine'

# Mangum adapter to run FastAPI on AWS Lambda
handler = Mangum(app)
