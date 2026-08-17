from django.db import models
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password
from django.core.validators import MinValueValidator, MaxValueValidator


class User(models.Model):
    username = models.CharField(max_length=200, unique=True)
    password = models.CharField(max_length=200)
    phonenumber = models.CharField(max_length=200)
    email = models.EmailField(max_length=200)
    isActive = models.BooleanField(default=False)

    def __str__(self):
        return self.username
    



class Admin(models.Model):
    username = models.CharField(max_length=200, unique=True)
    password = models.CharField(max_length=200)
    last_login = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.username   
    

class Owner(models.Model):
    name = models.CharField(max_length=100, unique=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, unique=True)
    
    password = models.CharField(max_length=255)
    isActive = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def __str__(self):
        return self.name


class Driver(models.Model):
    name = models.CharField(max_length=100, unique=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, unique=True)
    license_number = models.CharField(max_length=50, unique=True)
    license_expiry = models.DateField(null=True, blank=True)
    experience_years = models.PositiveIntegerField(default=0)
    password = models.CharField(max_length=255)
    is_available = models.BooleanField(default=False)
    isActive = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    STATUS_CHOICES = [
        ('available', 'Available'),
        ('on_trip', 'On Trip'),
        ('offline', 'Offline'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='offline')

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def __str__(self):
        return self.name        
    


class OwnerOTP(models.Model):
    phonenumber = models.CharField(max_length=15)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.created_at + timezone.timedelta(minutes=5)

    def __str__(self):
        return self.phonenumber    




class PhoneOTP(models.Model):
    phonenumber = models.CharField(max_length=15, unique=True)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    

    
    def is_expired(self):
        return timezone.now() > self.created_at + timezone.timedelta(minutes=5)

    def __str__(self):
        return f"{self.phone_number} - {self.otp}"
    


    

class Car(models.Model):

    CAR_TYPE_CHOICES = (
        ('sedan', 'Sedan'),
        ('suv', 'SUV'),
        ('hatchback', 'Hatchback'),
        ('luxury', 'Luxury'),
    )

    FUEL_CHOICES = (
        ('petrol', 'Petrol'),
        ('diesel', 'Diesel'),
        ('cng', 'CNG'),
        ('electric', 'Electric'),
    )

    TRANSMISSION_CHOICES = (
        ('Manual', 'Manual'),
        ('Automatic', 'Automatic'),
    )

    STATUS = (
        ('available', 'Available'),
        ('running', 'Running'),
        
        ('maintenance', 'Maintenance'),
    )

    name = models.CharField(max_length=100)
    brand = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    variant = models.CharField(max_length=100)  
    place = models.CharField(max_length=100)
    landmark = models.CharField(max_length=150, default="Near Railway Station")  # NEW FIELD

    car_type = models.CharField(max_length=20, choices=CAR_TYPE_CHOICES)
    status = models.CharField(max_length=50, choices=STATUS,default="Available")
    fuel_type = models.CharField(max_length=20, choices=FUEL_CHOICES)
    transmission = models.CharField(max_length=20, choices=TRANSMISSION_CHOICES)

    seats = models.PositiveIntegerField()
    price_per_hour = models.PositiveIntegerField()

    image = models.ImageField(upload_to='cars/', null=True, blank=True)
    available = models.BooleanField(default=True)
    owner = models.ForeignKey(Owner, on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.brand} {self.model} ({self.variant})"
    



# ----------------------------------------------------
# ✅ NEW BOOKING MODEL
# ----------------------------------------------------
# models.py
class Booking(models.Model):



    user = models.ForeignKey(User, on_delete=models.CASCADE)

    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    want_driver = models.BooleanField(default=False)
    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, blank=True)

    pickup_location = models.CharField(max_length=100, default="")
    drop_location = models.CharField(max_length=100, default="")

    pickup_datetime = models.DateTimeField()
    drop_datetime = models.DateTimeField()
    

    total_hours = models.IntegerField(default=1)
    total_price = models.IntegerField(default=0)

    payment_status = models.CharField(max_length=20, default="PENDING")
    status = models.CharField(max_length=20, default="STARTED")
    created_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(Owner, on_delete=models.CASCADE)
    order_id = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"Booking #{self.id} → {self.car.name}"
    


class Favourite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'car')  # Prevent duplicate favourites




class Review(models.Model):
    # One booking can have only one review
    
    
    # We also link to Car and User for easy querying later (e.g., "Show all reviews for this Car")
    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)
    
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5"
    )
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.car.name} ({self.rating}★)"        


class ChatMessage(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)

    sender_id = models.IntegerField()
    sender_type = models.CharField(max_length=10)   # "user" or "driver"

    receiver_id = models.IntegerField()
    receiver_type = models.CharField(max_length=10)

    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)