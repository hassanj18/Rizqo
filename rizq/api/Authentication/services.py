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
    def validate_cnic_gender(cnic: str, gender: str) -> tuple[bool, str]:
        """
        Validate CNIC last digit against gender encoding.
        Pakistani CNIC encoding: Male (1,3,5,7,9), Female (2,4,6,8,0)
        Returns (is_valid, error_message)
        """
        if not cnic or len(cnic) != 13:
            return False, "CNIC must be exactly 13 digits"
        
        last_digit = int(cnic[-1])
        gender_lower = gender.lower()
        
        print("Gender is:- ", gender)
        print("CNIC is:- ", cnic)
        print("Last digit is:- ", last_digit)
        # print("Gender is:- ", gender_lower)
        if gender_lower == "male":
            if last_digit not in [1, 3, 5, 7, 9]:
                return False, "CNIC gender decoding failure.😎"
        elif gender_lower == "female":
            if last_digit not in [2, 4, 6, 8, 0]:
                return False, "CNIC gender decoding failure.😎"
        elif gender_lower == "other":
            # For "other" gender, we don't validate CNIC encoding
            return True, ""
        else:
            return False, "Invalid gender. Please select Male, Female, or Other"
        
        return True, ""

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
        otp_expiry = timezone.now() + datetime.timedelta(minutes=30)  # Increased to 30 minutes
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
        "Generate a 6 Digit OTP and store in cache with CNIC"
        otp = str(random.randint(100000, 999999))  # 6-digit OTP

        print(f"Generated OTP: {otp} for CNIC: {cnic}")
        cache_key = f"otp_{cnic}"
        cache.set(cache_key, otp, timeout=1800)  # OTP valid for 30 mins (1800 seconds)
        
        # Verify it was stored
        stored_otp = cache.get(cache_key)
        print(f"OTP stored in cache: {stored_otp}")
        print(f"Cache key: {cache_key}")
        
        return otp     
    
    @staticmethod   
    def verify_cache_otp(cnic, otp):
        cache_key = f"otp_{cnic}"
        cached_otp = cache.get(cache_key)
        print(f"Verifying OTP for CNIC: {cnic}")
        print(f"Cache key: {cache_key}")
        print(f"Submitted OTP: {otp}")
        print(f"Cached OTP: {cached_otp}")
        print(f"OTP match: {cached_otp == otp}")
        
        if cached_otp and cached_otp == otp:
            cache.delete(cache_key)  # OTP used once
            print(f"OTP verified successfully for CNIC: {cnic}")
            return True
        print(f"OTP verification failed for CNIC: {cnic}")
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
