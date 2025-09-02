import os
import requests

# Load values from environment variables
SMS_BASE_URL = os.getenv("SMS_BASE_URL")
SMS_API_KEY = os.getenv("SMS_API_KEY")
SMS_DEVICE_ID = os.getenv("SMS_DEVICE_ID")

def send_msg(phone: str, msg: str):
    """
    Send OTP via SMS using TextBee API.
    """
    url = f"{SMS_BASE_URL}/gateway/devices/{SMS_DEVICE_ID}/send-sms"

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

# send_otp("03333557903","123654")