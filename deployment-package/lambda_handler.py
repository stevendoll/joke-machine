import json
import os
from main import app
from mangum import Mangum

# Mangum adapter to run FastAPI on AWS Lambda
handler = Mangum(app)
