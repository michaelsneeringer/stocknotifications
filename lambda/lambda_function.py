"""
Daily Stock Chart Email Notification Lambda Function

Fetches a stock chart image from StockCharts.com and emails it via Gmail SMTP.
"""

import json
import os
import ssl
import smtplib
import urllib.request
from datetime import datetime
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import boto3


def get_gmail_app_password():
    """Retrieve Gmail App Password from AWS Secrets Manager."""
    client = boto3.client("secretsmanager")
    response = client.get_secret_value(SecretId=os.environ["SECRET_ARN"])
    secret = json.loads(response["SecretString"])
    return secret["gmail_app_password"]


def fetch_chart_image():
    """Fetch the stock chart image from StockCharts.com.

    The CHART_IMAGE_URL environment variable should point to a direct image endpoint.
    StockCharts serves chart images from their c-sc/sc endpoint using permalink IDs.
    """
    url = os.environ["CHART_IMAGE_URL"]
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "image/png,image/jpeg,image/*,*/*",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        content_type = response.headers.get("Content-Type", "")
        data = response.read()

        if len(data) < 1000:
            raise ValueError(
                f"Response too small ({len(data)} bytes) - likely not a chart image. "
                "Check CHART_IMAGE_URL environment variable."
            )

        return data, content_type


def send_email(image_data, content_type):
    """Send email with the chart image embedded inline."""
    sender = os.environ["SENDER_EMAIL"]
    recipient = os.environ["RECIPIENT_EMAIL"]
    password = get_gmail_app_password()

    today = datetime.now().strftime("%B %d, %Y")

    msg = MIMEMultipart("related")
    msg["Subject"] = f"Daily $SPX Chart - {today}"
    msg["From"] = sender
    msg["To"] = recipient

    html_body = MIMEText(
        f"<html><body>"
        f"<h2>Daily $SPX Stock Chart</h2>"
        f"<p>{today}</p>"
        f'<img src="cid:chart" style="max-width:100%;">'
        f"</body></html>",
        "html",
    )
    msg.attach(html_body)

    # Determine image subtype from Content-Type
    if "jpeg" in content_type or "jpg" in content_type:
        subtype = "jpeg"
    elif "gif" in content_type:
        subtype = "gif"
    else:
        subtype = "png"

    image = MIMEImage(image_data, _subtype=subtype)
    image.add_header("Content-ID", "<chart>")
    image.add_header("Content-Disposition", "inline", filename=f"spx_chart.{subtype}")
    msg.attach(image)

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender, password)
        server.sendmail(sender, recipient, msg.as_string())

    print(f"Email sent to {recipient}")


def handler(event, context):
    """AWS Lambda handler."""
    print("Fetching chart image...")
    image_data, content_type = fetch_chart_image()
    print(f"Chart image fetched: {len(image_data)} bytes, type: {content_type}")

    print("Sending email...")
    send_email(image_data, content_type)

    return {"statusCode": 200, "body": "Chart email sent successfully"}
