from django.db import models

# Create your models here.


from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


class CustomUserManager(BaseUserManager):
    def create_user(self, cnic, phone, dob, full_name, gender, **extra_fields):
        if not cnic:
            raise ValueError("CNIC is required")
        if not full_name:
            raise ValueError("Full name is required")
        if not gender:
            raise ValueError("Gender is required")

        user = self.model(
            cnic=cnic,
            phone=phone,
            dob=dob,
            full_name=full_name,
            gender=gender,
            **extra_fields
        )
        user.save(using=self._db)
        return user

    def create_superuser(self, cnic, phone, dob, full_name, gender, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        return self.create_user(cnic, phone, dob, full_name, gender, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    cnic_validator = RegexValidator(
        regex=r'^\d{13}$',
        message="CNIC must be exactly 13 digits."
    )
    GENDER_CHOICES = [
    ("male", "Male"),
    ("female", "Female"),
    ("other", "Other"),
    ]
    full_name = models.CharField(max_length=255,null=False,blank=False)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES,null=False,blank=False)
    cnic = models.CharField(
        max_length=13,
        unique=True,
        primary_key=True,
        validators=[cnic_validator]
    )
    phone = models.CharField(max_length=11,unique=True, blank=False, null=False, validators=[RegexValidator(
    regex=r"^\d{11}", message="Phone number must be 11 digits only.")])
    dob = models.DateField()

    #OTP details are here
    otp = models.CharField(max_length=6, null=True, blank=True)
    otp_expiry = models.DateTimeField(blank=True, null=True)
    max_otp_try = models.CharField(max_length=2, default=3)
    otp_max_out = models.DateTimeField(blank=True, null=True)
    # required by Django admin
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = "cnic"
    REQUIRED_FIELDS = ["phone", "dob", "full_name", "gender"]

    def __str__(self):
        return self.cnic

    # override password-related methods (disable them)
    def set_password(self, raw_password):
        pass

    def check_password(self, raw_password):
        return False
