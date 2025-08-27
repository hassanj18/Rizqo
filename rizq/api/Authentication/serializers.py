from rest_framework import serializers
from .. models import CustomUser   # assuming your model is named CustomUser

class SignUpSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['full_name', 'gender', 'cnic', 'phone', 'dob']

    # (optional) you can add extra validations
    def validate_phone(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("Phone number must be digits only.")
        return value
