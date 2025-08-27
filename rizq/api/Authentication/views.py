from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from .services import OTPService
from rest_framework.decorators import api_view,permission_classes
from ..SMS_Gateway.SMS_Functions import send_msg
from rest_framework import viewsets
from ..models import CustomUser
from .serializers import SignUpSerializer
class LoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request, *args, **kwargs):
        cnic = request.data.get("cnic")
        if not cnic:
            return Response({"message": "CNIC is required"}, status=status.HTTP_400_BAD_REQUEST)
        user, error = OTPService.get_user(cnic)
        if not user:
            return Response({"message": error}, status=status.HTTP_404_NOT_FOUND)
        user, error = OTPService.set_user_otp(user)
        if error: 
            return Response({"message": error}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": "Successfully generated OTP"}, status=status.HTTP_200_OK)

class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        otp = request.data.get("otp")
        if not otp:
            return Response({"message": "OTP is required"}, status=status.HTTP_400_BAD_REQUEST)

        tokens, error = OTPService.verify_otp(request, otp)
        if error:
            return Response({"message": error}, status=status.HTTP_400_BAD_REQUEST)

        return Response(tokens, status=status.HTTP_200_OK) 

@api_view(['POST'])
@permission_classes([AllowAny])
def request_signup_otp(request):
    """ Takes in input cnic and phone"""
    cnic = request.data.get("cnic")
    phone = request.data.get("phone")
    if not cnic:
        return Response({"error": "CNIC is required"}, status=status.HTTP_400_BAD_REQUEST)
    if not phone:
        return Response({"error": "phone is required"}, status=status.HTTP_400_BAD_REQUEST)

    otp = OTPService.generate_cache_otp(cnic)
    send_msg(phone,otp)
    return Response({"message": "OTP sent"}, status=status.HTTP_200_OK)

class SignupViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = SignUpSerializer
    permission_classes = [AllowAny]
    def create(self, request, *args, **kwargs):
        otp = request.data.get("otp")
        cnic = request.data.get("cnic")
        print(otp)
        print(cnic)
        print(request.data)
        if not otp or not cnic:
            return Response({"error": "CNIC and OTP are required"}, status=status.HTTP_400_BAD_REQUEST)

        if not OTPService.verify_cache_otp(cnic, otp):
            return Response({"error": "Invalid or expired OTP"}, status=status.HTTP_400_BAD_REQUEST)

        return super().create(request, *args, **kwargs)