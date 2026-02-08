from main import app
from mangum import Mangum
from aws_lambda_powertools import Logger, Tracer, Metrics

# Initialize Powertools
logger = Logger(service="joke-machine")
tracer = Tracer(service="joke-machine")
metrics = Metrics(service="joke-machine")

# Mangum adapter to run FastAPI on AWS Lambda with Powertools integration
handler = Mangum(app)
