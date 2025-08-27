from django.contrib import admin
from django.urls import path
from .Authentication.views import *

urlpatterns = [
    # Auth+OTP auth endpoints
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('auth/request-signup-otp/', request_signup_otp, name='request-otp'),
    path('auth/signup/',SignupViewSet.as_view({'post':'create'}),name='signup')
] 
