#!/usr/bin/env bash
set -euo pipefail

#
# Deploy the Daily Stock Chart Email Notification stack.
#
# Prerequisites:
#   - AWS CLI v2 installed and configured (aws configure)
#   - A Gmail App Password (https://myaccount.google.com/apppasswords)
#
# Usage:
#   ./deploy.sh
#

STACK_NAME="daily-stock-chart-email"
REGION="${AWS_DEFAULT_REGION:-us-west-2}"
S3_BUCKET="${STACK_NAME}-deployment-${REGION}"

echo "=== Daily Stock Chart Email - Deployment ==="
echo ""

# Prompt for Gmail App Password
read -sp "Enter your Gmail App Password: " GMAIL_APP_PASSWORD
echo ""

if [ -z "$GMAIL_APP_PASSWORD" ]; then
    echo "Error: Gmail App Password cannot be empty."
    exit 1
fi

# Create S3 bucket for deployment artifacts (if it doesn't exist)
echo "Ensuring deployment S3 bucket exists..."
if ! aws s3api head-bucket --bucket "$S3_BUCKET" 2>/dev/null; then
    aws s3api create-bucket \
        --bucket "$S3_BUCKET" \
        --region "$REGION" \
        --create-bucket-configuration LocationConstraint="$REGION"
    echo "Created bucket: $S3_BUCKET"
else
    echo "Bucket already exists: $S3_BUCKET"
fi

# Package the CloudFormation template (uploads Lambda code to S3)
echo "Packaging CloudFormation template..."
aws cloudformation package \
    --template-file template.yaml \
    --s3-bucket "$S3_BUCKET" \
    --output-template-file packaged-template.yaml \
    --region "$REGION"

# Deploy the stack
echo "Deploying CloudFormation stack: $STACK_NAME ..."
aws cloudformation deploy \
    --template-file packaged-template.yaml \
    --stack-name "$STACK_NAME" \
    --capabilities CAPABILITY_NAMED_IAM \
    --region "$REGION" \
    --parameter-overrides \
        GmailAppPassword="$GMAIL_APP_PASSWORD"

echo ""
echo "=== Deployment Complete ==="
echo ""

# Show outputs
aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --query "Stacks[0].Outputs" \
    --output table

echo ""
echo "To test the Lambda function manually:"
echo "  aws lambda invoke --function-name daily-stock-chart-email --region $REGION /dev/stdout"
echo ""
echo "To view logs:"
echo "  aws logs tail /aws/lambda/daily-stock-chart-email --region $REGION --follow"
