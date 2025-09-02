from rest_framework import serializers
from ..models import CustomUser

class SignUpSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['full_name', 'gender', 'cnic', 'phone', 'dob', 'password']
        # Remove read_only_fields since we need CNIC for creation

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print("=== SERIALIZER INIT ===")
        print(f"Args: {args}")
        print(f"Kwargs: {kwargs}")
        if 'data' in kwargs:
            print(f"Data received: {kwargs['data']}")
        print("======================")

    def validate_phone(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("Phone number must be digits only.")
        return value
    
    def validate_cnic(self, value):
        if not value:
            raise serializers.ValidationError("CNIC is required.")
        if len(value) != 13:
            raise serializers.ValidationError("CNIC must be exactly 13 digits.")
        return value
    
    def validate_gender(self, value):
        # Convert 'male' to 'M', 'female' to 'F', etc.
        gender_mapping = {
            'male': 'M',
            'female': 'F', 
            'other': 'O',
            'M': 'M',
            'F': 'F',
            'O': 'O'
        }
        return gender_mapping.get(value.lower(), value)
    
    def validate_dob(self, value):
        # If value is a string, try to parse it
        if isinstance(value, str):
            try:
                from datetime import datetime
                # Try different date formats
                for fmt in ['%d/%m/%Y', '%Y-%m-%d', '%m/%d/%Y']:
                    try:
                        return datetime.strptime(value, fmt).date()
                    except ValueError:
                        continue
                raise serializers.ValidationError("Invalid date format. Use DD/MM/YYYY or YYYY-MM-DD")
            except Exception as e:
                raise serializers.ValidationError(f"Invalid date: {e}")
        return value
    
    def create(self, validated_data):
        print("=== CREATE METHOD DEBUG ===")
        print(f"Validated data: {validated_data}")
        print(f"Validated data keys: {list(validated_data.keys())}")
        
        # Extract required fields explicitly
        cnic = validated_data.get('cnic')
        phone = validated_data.get('phone')
        dob = validated_data.get('dob')
        full_name = validated_data.get('full_name')
        gender = validated_data.get('gender')
        
        print(f"Extracted fields:")
        print(f"  CNIC: {cnic}")
        print(f"  Phone: {phone}")
        print(f"  DOB: {dob}")
        print(f"  Full Name: {full_name}")
        print(f"  Gender: {gender}")
        
        # Create user with explicit parameters
        user = CustomUser.objects.create_user(
            cnic=cnic,
            phone=phone,
            dob=dob,
            full_name=full_name,
            gender=gender
        )
        
        # Handle password if provided
        password = validated_data.get('password')
        if password:
            user.set_password(password)
            user.save()
        
        print(f"User created successfully: {user}")
        print("==========================")
        return user
