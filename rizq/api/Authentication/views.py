from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
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
        print(f"😀😀😀{otp}")
        if not otp:
            return Response({"message": "OTP is required"}, status=status.HTTP_400_BAD_REQUEST)

        tokens, error = OTPService.verify_otp(request, otp)
        print(f"🤣🤣🤣{tokens}")
        print(f"🤣🤣🤣{error}")
        if error:
            return Response({"message": error}, status=status.HTTP_400_BAD_REQUEST)

        # Get user data from the request (set by OTPService.verify_otp)
        user = request.user
        user_data = {
            "cnic": user.cnic,
            "full_name": user.full_name,
            "phone": user.phone,
            "gender": user.gender,
            "dob": user.dob.strftime('%Y-%m-%d') if user.dob else None,
        }

        return Response({
            "tokens": tokens,
            "user": user_data
        }, status=status.HTTP_200_OK) 

@api_view(['POST'])
@permission_classes([AllowAny])
def request_signup_otp(request):
    """ Takes in input cnic, phone, fullName, gender, and dob"""
    cnic = request.data.get("cnic")
    phone = request.data.get("phone")
    fullName = request.data.get("fullName")
    gender = request.data.get("gender")
    dob = request.data.get("dob")
    
    if not cnic:
        return Response({"error": "CNIC is required"}, status=status.HTTP_400_BAD_REQUEST)
    if not phone:
        return Response({"error": "phone is required"}, status=status.HTTP_400_BAD_REQUEST)
    if not fullName:
        return Response({"error": "fullName is required"}, status=status.HTTP_400_BAD_REQUEST)
    if not gender:
        return Response({"error": "gender is required"}, status=status.HTTP_400_BAD_REQUEST)
    if not dob:
        return Response({"error": "dob is required"}, status=status.HTTP_400_BAD_REQUEST)

    # Block if CNIC or phone is already registered
    if CustomUser.objects.filter(cnic=cnic).exists():
        return Response({"message": "This CNIC is already registered."}, status=status.HTTP_400_BAD_REQUEST)
    if CustomUser.objects.filter(phone=phone).exists():
        return Response({"message": "This phone no. is already registered."}, status=status.HTTP_400_BAD_REQUEST)

    print(f"=== OTP REQUEST DEBUG ===")
    print(f"CNIC: {cnic}")
    print(f"Phone: {phone}")
    print(f"Full Name: {fullName}")
    print(f"Gender: {gender}")
    print(f"DOB: {dob}")
    print(f"=========================")

    # Store signup data temporarily (you might want to use cache or session)
    # For now, we'll just generate OTP
    otp = OTPService.generate_cache_otp(cnic)
    send_msg(phone, otp)
    
    return Response({"message": "OTP sent"}, status=status.HTTP_200_OK)

class SignupViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = SignUpSerializer
    permission_classes = [AllowAny]
    def create(self, request, *args, **kwargs):
        otp = request.data.get("otp")
        cnic = request.data.get("cnic")
        print("=== SIGNUP DEBUG ===")
        print(f"OTP: {otp}")
        print(f"CNIC: {cnic}")
        print(f"Full request data: {request.data}")
        print(f"Data type: {type(request.data)}")
        print(f"Keys: {list(request.data.keys()) if hasattr(request.data, 'keys') else 'No keys'}")
        print("===================")
        
        if not otp or not cnic:
            return Response({"error": "CNIC and OTP are required"}, status=status.HTTP_400_BAD_REQUEST)

        if not OTPService.verify_cache_otp(cnic, otp):
            return Response({"error": "Invalid or expired OTP"}, status=status.HTTP_400_BAD_REQUEST)

        # Map frontend field names to backend field names
        signup_data = {
            'full_name': request.data.get('full_name') or request.data.get('fullName'),
            'cnic': request.data.get('cnic'),
            'phone': request.data.get('phone'),
            'gender': request.data.get('gender'),
            'dob': request.data.get('dob'),
            'password': request.data.get('password', 'defaultPassword123')
        }

        # Create serializer instance with the mapped data
        serializer = self.get_serializer(data=signup_data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "message": "User created successfully",
                "user": {
                    "cnic": user.cnic,
                    "full_name": user.full_name,
                    "phone": user.phone,
                    "gender": user.gender,
                    "dob": user.dob
                }
            }, status=status.HTTP_201_CREATED)
        else:
            print("=== SERIALIZER ERRORS ===")
            print(f"Validation errors: {serializer.errors}")
            print(f"Validated data: {serializer.validated_data}")
            print("=========================")
            
            # Convert serializer errors to user-friendly messages
            error_messages = []
            for field, errors in serializer.errors.items():
                if field == 'phone' and 'unique' in str(errors):
                    error_messages.append("A user with this phone number already exists. Please use a different phone number or try logging in instead.")
                elif field == 'cnic' and 'unique' in str(errors):
                    error_messages.append("A user with this CNIC already exists. Please use a different CNIC or try logging in instead.")
                else:
                    for error in errors:
                        error_messages.append(f"{field.replace('_', ' ').title()}: {error}")
            
            return Response({
                "error": "Validation failed",
                "details": error_messages
            }, status=status.HTTP_400_BAD_REQUEST)

class TokenVerificationView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        """Verify JWT token and return user data"""
        try:
            user = request.user
            user_data = {
                "cnic": user.cnic,
                "full_name": user.full_name,
                "phone": user.phone,
                "gender": user.gender,
                "dob": user.dob.strftime('%Y-%m-%d') if user.dob else None,
            }
            
            return Response({
                "valid": True,
                "user": user_data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "valid": False,
                "error": "Token verification failed"
            }, status=status.HTTP_401_UNAUTHORIZED)