#!/usr/bin/env python3
"""
Local test script for the stock chart email Lambda function.

Usage:
    pip install boto3
    python test_local.py
"""

import os
import sys

sys.path.insert(0, "lambda")

os.environ["CHART_IMAGE_URL"] = (
    "https://stockcharts.com/c-sc/sc?s=$SPX&p=D&id=p95318658468"
)
os.environ["SENDER_EMAIL"] = "michaelsneeringer@gmail.com"
os.environ["RECIPIENT_EMAIL"] = "michaelsneeringer@me.com"

import lambda_function

# Bypass Secrets Manager for local testing
lambda_function.get_gmail_app_password = lambda: "wuwh ipjb asgp smku"

# Run the handler
result = lambda_function.handler({}, None)
print(result)
