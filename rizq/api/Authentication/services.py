import random
import datetime
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from ..models import CustomUser
from ..SMS_Gateway.SMS_Functions import send_msg
from django.contrib.auth import authenticate, login
import random
from django.core.cache import cache
from rest_framework_simplejwt.tokens import RefreshToken

class OTPService:
    @staticmethod
    def generate_otp():
        """Generate a 4-digit OTP"""
        return random.randint(100000, 999999)

    @staticmethod
    def set_user_otp(user: CustomUser):
        """Handles OTP logic: expiry, tries, lockout, save and send"""

        # Check for max OTP attempts
        if int(user.max_otp_try) == 0 and user.otp_max_out and timezone.now() < user.otp_max_out:
            return None, "Max OTP try reached, try after an hour"

        # Generate OTP
        otp = OTPService.generate_otp()
        otp_expiry = timezone.now() + datetime.timedelta(minutes=10)
        max_otp_try = int(user.max_otp_try) - 1

        # Update user object
        user.otp = otp
        user.otp_expiry = otp_expiry
        user.max_otp_try = max_otp_try

        if max_otp_try == 0:
            user.otp_max_out = timezone.now() + datetime.timedelta(hours=1)
        elif max_otp_try == -1:  # reset after lockout
            user.max_otp_try = 3
        else:
            user.otp_max_out = None

        user.save()

        # Send OTP (using CNIC instead of phone for logging)
        send_msg(user.phone, otp)
        return user, None

    @staticmethod
    def get_user(cnic: str):
        """Fetch user by CNIC or create a new one"""
        try:
            return CustomUser.objects.get(cnic=cnic), False
        except ObjectDoesNotExist:
            return None,"User Does Not Exist"
    @staticmethod   
    def generate_cache_otp(cnic):
        "Generat a 6 Digit OTP and store in cache with CNIC"
        otp = str(random.randint(100000, 999999))  # 6-digit OTP
        cache_key = f"otp_{cnic}"
        cache.set(cache_key, otp, timeout=300)  # OTP valid for 5 mins
        return otp     
    @staticmethod
    def verify_cache_otp(cnic, otp):
        cache_key = f"otp_{cnic}"
        cached_otp = cache.get(cache_key)
        if cached_otp and cached_otp == otp:
            cache.delete(cache_key)  # OTP used once
            return True
        return False
    @staticmethod
    def verify_otp(request, otp: str):
        """Verify OTP, reset user state, return JWT token if valid"""
        try:
            user = CustomUser.objects.get(otp=otp)
        except ObjectDoesNotExist:
            return None, "Please enter the correct OTP"

        # Check expiry
        if user.otp_expiry and timezone.now() > user.otp_expiry:
            return None, "OTP has expired"

        # Login the user
        login(request, user)

        # Reset OTP fields
        user.otp = None
        user.otp_expiry = None
        user.max_otp_try = 3
        user.otp_max_out = None
        user.save()

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        tokens = {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }
        return tokens, None
