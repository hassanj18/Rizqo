import os
import requests

# Load values from environment variables
# SMS_BASE_URL = os.getenv("SMS_BASE_URL", "https://api.textbee.dev/api/v1")
# SMS_API_KEY = os.getenv("SMS_API_KEY")
# SMS_DEVICE_ID = os.getenv("SMS_DEVICE_ID")
SMS_BASE_URL="https://api.textbee.dev/api/v1"
SMS_API_KEY="0c45b9db-4006-4310-91c8-f04d64baead7"
SMS_DEVICE_ID="68adf41c27a25d62baa704a0"
def send_msg(phone: str, msg: str):
    """
    Send OTP via SMS using TextBee API.
    """
    url = f"{SMS_BASE_URL}/gateway/devices/68adf41c27a25d62baa704a0/send-sms"

    try:
        response = requests.post(
            url,
            json={
                "recipients": [phone],
                "message": msg
            },
            headers={"x-api-key": SMS_API_KEY},
            timeout=10
        )
        response.raise_for_status()  # Raise error if status != 200
        print(f"Message sent to {phone}: {msg}")
        return response.json()
    except requests.RequestException as e:
        print(f"Failed to send SMS: {e}")
        return None

def send_otp(phone: str, otp: str):
    send_msg(phone,f"Your One-Time-Password for Rizqo is {otp}")

send_otp("03333557903","123654")