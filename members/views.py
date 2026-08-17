import json

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from django.http import HttpResponse, JsonResponse
from requests import request
from .models import Car, Booking, ChatMessage,Owner,OwnerOTP,Favourite, Review ,Driver
from members.models import User
from datetime import date, datetime, timedelta
from django.db.models import Sum
from django.contrib.auth.hashers import make_password
from .models import User, PhoneOTP,Admin,Owner
from twilio.rest import Client
import random
from django.contrib.auth.decorators import login_required
import math
from django.utils import timezone
import razorpay
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import localdate, now
from django.core.mail import send_mail
from django.db.models import Case, When, Value, IntegerField
from django.db.models import Count, Q # Import Q for filtering










# -------------------- BASIC PAGES --------------------
from django.shortcuts import render, redirect
from django.utils.timezone import now
from .models import Car, Booking, Favourite  # Make sure Favourite is imported

def index(request):
    role = request.session.get("role")

    if role == "admin":
        return redirect("admin_dashboard")

    if role == "owner":
        return redirect("owner_dashboard")
    
    userid = request.session.get("user_id")
    # If you want the home page to be visible to non-logged-in users, 
    # you might want to remove this redirect. But based on your code:
    
    # 1. Fetch Featured Cars
    featured_cars = Car.objects.filter(
        available=True
    ).order_by("-id")[:8]

    # 2. [NEW] Calculate 'is_favourite' status for each car
    # We get a set of car IDs that this user has favourited
    my_fav_ids = set(Favourite.objects.filter(user_id=userid).values_list('car_id', flat=True))

    # We loop through the cars and manually add an attribute 'is_favourite'
    # This attribute is temporary (just for this request) and won't be saved to the DB
    for car in featured_cars:
        car.is_favourite = car.id in my_fav_ids

    # 3. Update Status Logic (Existing)
    Booking.objects.filter(
        user_id=userid,
        status="BOOKED",
        drop_datetime__lt=now()
    ).update(status="COMPLETED")


    recent_reviews = Review.objects.all().order_by('-created_at')[:6]

    return render(request, "index.html", {
        "featured_cars": featured_cars,
        "recent_reviews": recent_reviews,
    })

# -------------------- USER REGISTER --------------------


def send_otp(phone):
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    otp = str(random.randint(100000, 999999))

    client.messages.create(
        body=f"Your otp is {otp},please not share with anyone.",
        from_=settings.TWILIO_PHONE_NUMBER,
        to="+91" + phone,
    )
    PhoneOTP.objects.create(phonenumber=phone, otp=otp)
    return otp




def send_owner_otp(phone):
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    otp = str(random.randint(100000, 999999))

    client.messages.create(
        body=f"Your Owner OTP is {otp}. Do not share it with anyone.",
        from_=settings.TWILIO_PHONE_NUMBER,
        to="+91" + phone,
    )

    OwnerOTP.objects.update_or_create(
        phonenumber=phone,
        defaults={"otp": otp}
    )

    return otp





def verify_owner_otp(request, phone):

    if request.session.get("role") == "admin":
         return redirect("admin_dashboard")

    

    if request.session.get("role") == "customer":
        return redirect("index")
    
    if request.session.get("role") == "owner":
        return redirect("owner_dashboard")
    

    remaining_seconds = 0

    try:
        otp_obj = OwnerOTP.objects.get(phonenumber=phone)

        expiry_time = otp_obj.created_at + timezone.timedelta(minutes=5)
        remaining_seconds = int((expiry_time - timezone.now()).total_seconds())

        if remaining_seconds < 0:
            remaining_seconds = 0

        if request.method == "POST":
            user_otp = request.POST.get("otp")

            if otp_obj.is_expired():
                messages.error(request, "OTP expired. Please resend OTP.")
            elif otp_obj.otp == user_otp:
                owner = Owner.objects.get(phone=phone)
                owner.isActive = True
                owner.save()
                otp_obj.delete()
                return redirect("owner_login")
            else:
                messages.error(request, "Invalid OTP")

    except OwnerOTP.DoesNotExist:
        messages.error(request, "OTP not found")
        return redirect("owner_register")

    return render(
        request,
        "owner/verify_owner_otp.html",
        {
            "phone": phone,
            "remaining_seconds": remaining_seconds
        }
    )



def verify_otp(request):

    if request.session.get("role") == "admin":
         return redirect("admin_dashboard")

    

    if request.session.get("role") == "customer":
        return redirect("index")
    
    if request.session.get("role") == "owner":
        return redirect("owner_dashboard")
    


    if request.method == "POST":
        phone = request.POST.get("phone")
        user_otp = request.POST.get("otp")

        try:
            otp_obj = PhoneOTP.objects.get(phonenumber=phone)

            if otp_obj.is_expired():
                messages.error(request, "OTP expired.Please try again")
                return render(request, "register.html")
            if otp_obj.otp == user_otp:
                user = User.objects.get(phonenumber=phone)
                user.isActive = True
                user.save()
                otp_obj.delete()

                return redirect("login")
            else:
                messages.error(request, "incorrect otp")
                return render(request, "verify_otp.html", {"phone": phone})
        except PhoneOTP.DoesNotExist:
            messages.error(request, "phone not found")
            return redirect("verify_otp")
    return render(request, "verify_otp.html", {"phone": phone})




def resend_owner_otp(request, phone):
    try:
        owner = Owner.objects.get(phone=phone)

        if owner.isActive:
            messages.info(request, "Your account is already verified.")
            return redirect("owner_login")

        # 🔁 resend OTP
        send_owner_otp(phone)

        messages.success(request, "A new OTP has been sent to your phone.")
        return redirect("verify_owner_otp", phone=phone)

    except Owner.DoesNotExist:
        messages.error(request, "Owner not found.")
        return redirect("owner_register")



# -------------------- REGISTER --------------------


def register(request):
    messages.get_messages(request)


    if request.session.get("role") == "admin":
         return redirect("admin_dashboard")

    

    if request.session.get("role") == "customer":
        return redirect("index")
    
    if request.session.get("role") == "owner":
        return redirect("owner_dashboard")
    

    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        phonenumber = request.POST.get("phonenumber")
        password = request.POST.get("password")

        # 🔐 Check duplicate user
        if User.objects.filter(username=username).exists():
            messages.error(request, "username already registered.")
            return render(request, "register.html")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return render(request, "register.html")

        if User.objects.filter(phonenumber=phonenumber).exists():
            messages.error(request, "Phone number already registered.")
            return render(request, "register.html")

        # 🔐 Create inactive user with hashed password
        user = User.objects.create(
            username=username,
            email=email,
            phonenumber=phonenumber,
            password=make_password(password),
            isActive=False,
        )

        otp = send_otp(phonenumber)

        return render(request, "verify_otp.html", {"phone": phonenumber})

        # Redirect to OTP verify page

    return render(request, "register.html")



def owner_register(request):
    messages.get_messages(request)

    if request.session.get("role") == "admin":
         return redirect("admin_dashboard")

    

    if request.session.get("role") == "customer":
        return redirect("index")
    
    if request.session.get("role") == "owner":
        return redirect("owner_dashboard")
    

    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return redirect("owner_register")

        if Owner.objects.filter(phone=phone).exists():
            messages.error(request, "Owner already registered")
            return redirect("owner_register")

        # Create inactive owner
        owner = Owner.objects.create(
            name=name,
            email=email,
            phone=phone,
            isActive=False
        )
        owner.set_password(password)
        owner.save()

        # Send OTP
        send_owner_otp(phone)

        return redirect("verify_owner_otp", phone=phone)

    return render(request, "owner/register.html")



# -------------------- LOGIN --------------------


def login(request):
    messages.get_messages(request)

    if request.session.get("role") == "admin":
         return redirect("admin_dashboard")

    

    if request.session.get("role") == "customer":
        return redirect("index")
    
    if request.session.get("role") == "owner":
        return redirect("owner_dashboard")
    

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        # =========================
        # 1️⃣ ADMIN LOGIN (CUSTOM)
        # =========================
        try:
            admin = Admin.objects.get(username=username)

            if not admin.is_active:
                messages.error(request, "Admin account disabled.")
                return render(request, "login.html")

            if not check_password(password, admin.password):
                messages.error(request, "Invalid username or password.")
                return render(request, "login.html")

            # ✅ ADMIN LOGIN SUCCESS
            request.session.flush()
            request.session["admin_id"] = admin.id
            request.session["admin_username"] = admin.username
            request.session["role"] = "admin"

            admin.last_login = timezone.now()
            admin.save()

            return redirect("admin_dashboard")

        except Admin.DoesNotExist:
            pass  # continue to user login

        # =========================
        # 2️⃣ CUSTOMER LOGIN
        # =========================
        try:
            user = User.objects.get(username=username)

            if not check_password(password, user.password):
                messages.error(request, "Invalid username or password.")
                return render(request, "login.html")

            if not user.isActive:
                messages.error(request, "Account not active.")
                return render(request, "login.html")

            # ✅ CUSTOMER LOGIN SUCCESS
            request.session.flush()
            request.session["user_id"] = user.id
            request.session["username"] = user.username
            request.session["role"] = "customer"

            return redirect("index")

        except User.DoesNotExist:
            messages.error(request, "Invalid username or password.")

    return render(request, "login.html")









def owner_login(request):
    messages.get_messages(request)


    if request.session.get("role") == "admin":
         return redirect("admin_dashboard")

    

    if request.session.get("role") == "customer":
        return redirect("index")
    
    if request.session.get("role") == "owner":
        return redirect("owner_dashboard")
    


    if request.method == "POST":
        name = request.POST["name"]
        password = request.POST["password"]

        try:
            owner = Owner.objects.get(name=name)
            if owner.check_password(password):
                
                request.session.flush()
                request.session["owner_id"] = owner.id
                request.session["username"] = owner.name
                request.session["role"] = "owner"
                return redirect("owner_dashboard")
            else:
                messages.error(request, "Invalid password")
                return render(request, "owner/login.html")
        except Owner.DoesNotExist:
            messages.error(request, "Owner not found")
            return render(request, "owner/login.html")

    return render(request, "owner/login.html")




# -------------------- LOGOUT --------------------
def logout(request):
    request.session.flush()  # clears all session data

    return redirect("index")


# -------------------- OWNER DASHBOARD --------------------



def owner_dashboard(request):

    if request.session.get("role") != "owner":
        return redirect("login")

    ownerid = request.session.get("owner_id")
    if not ownerid:
        return redirect("login")

    owner = Owner.objects.get(id=ownerid)

    Booking.objects.filter(
    owner_id=ownerid,
    drop_datetime__lt=now()).exclude(
    status="CANCELLED").update(status="COMPLETED")

    # OWNER CARS
    cars = Car.objects.filter(owner_id=ownerid).annotate(
        booking_count=Count(
            'booking', 
            filter=Q(booking__status='BOOKED') | Q(booking__status='Running') | Q(booking__status='Pending')
        )
    ).order_by('-id')



    total_cars = cars.count()

    reviews = Review.objects.filter(car__in=cars).order_by('-created_at')

    Booking.objects.filter(
    owner_id=ownerid,
    status="BOOKED",
    drop_datetime__lt=now()
     ).update(status="COMPLETED")
    

    # BOOKINGS FOR OWNER
    bookings = Booking.objects.filter(owner_id=ownerid).annotate(
    status_priority=Case(
        When(status="BOOKED", then=Value(1)),
        default=Value(2),
        output_field=IntegerField(),
    )
).order_by("status_priority", "-created_at")
    


    
    total_bookings = bookings.count()

    # REVENUE
    completed_revenue = (
        bookings.filter(status="COMPLETED")
        .aggregate(total=Sum("total_price"))["total"] or 0
    )

    cancelled_revenue = (
        bookings.filter(status="CANCELLED")
        .aggregate(total=Sum("total_price"))["total"] or 0
    )

    upcoming_revenue = (
        bookings.filter(status="BOOKED")
        .aggregate(total=Sum("total_price"))["total"] or 0
    )

               

    daily_earnings = (
    bookings
    .filter(
        owner_id=ownerid,
        status="COMPLETED"
    )
    .values("created_at")
    .annotate(earnings=Sum("total_price"))
    .order_by("created_at")
     )

    booking_labels = []
    earnings_data = []

    for item in daily_earnings:
     if item["created_at"]:
        booking_labels.append(item["created_at"].strftime("%d %b"))
        earnings_data.append(item["earnings"])
   

    context = {
        "owner": owner,
        "cars": cars,
        "bookings": bookings,
        "total_cars": total_cars,
        'reviews': reviews,
        "total_bookings": total_bookings,
        "total_earnings": completed_revenue,
        "completed_revenue": completed_revenue,
        "upcoming_revenue": upcoming_revenue,
        "cancelled_revenue": cancelled_revenue,
        "booking_labels": booking_labels,
        "earnings_data": earnings_data,
    }

    return render(request, "owner/dashboard.html", context)


# -------------------- ADMIN DASHBOARD --------------------
from django.shortcuts import render, redirect
from django.db.models import Sum, Count
from django.db.models.functions import TruncDate, TruncMonth
from django.utils.timezone import now
from .models import User, Car, Booking

def admin_dashboard(request):
    # 1. Security Check
    if request.session.get("role") != "admin":
        return redirect("login")

    # 2. Auto-Complete Expired Bookings (Maintenance task)
    Booking.objects.filter(
        status="BOOKED",
        drop_datetime__lt=now()
    ).update(status="COMPLETED")

    # --- KPI CARDS DATA ---
    total_users = User.objects.count()
    total_cars = Car.objects.count()
    total_orders = Booking.objects.count()
    total_revenue = Booking.objects.aggregate(total=Sum("total_price"))["total"] or 0

    bookings = Booking.objects.filter(status="COMPLETED").order_by("-created_at")

    # --- GRAPH 1: MONTHLY REVENUE (Line Chart) ---
    # Group bookings by month and sum the price
    daily_earnings = (
    bookings
    .filter(
       
        status="COMPLETED"
    )
    .values("created_at")
    .annotate(earnings=Sum("total_price"))
    .order_by("created_at")
     )

    booking_labels = []
    earnings_data = []

    for item in daily_earnings:
     if item["created_at"]:
        booking_labels.append(item["created_at"].strftime("%d %b"))
        earnings_data.append(item["earnings"])
    # --- GRAPH 2: BOOKING STATUS (Doughnut Chart) ---
    status_counts = Booking.objects.values('status').annotate(count=Count('id'))
    status_dict = {item['status']: item['count'] for item in status_counts}
    
    # Order: Active, Completed, Cancelled
    status_labels = ['Active', 'Completed', 'Cancelled']
    status_values = [
        status_dict.get('BOOKED', 0),
        status_dict.get('COMPLETED', 0),
        status_dict.get('CANCELLED', 0)
    ]

    # --- GRAPH 3: TOP 5 POPULAR CARS (Bar Chart) ---
    top_cars = (
        Car.objects.annotate(booking_count=Count('booking'))
        .order_by('-booking_count')[:5]
    )
    car_labels = [car.name for car in top_cars]
    car_values = [car.booking_count for car in top_cars]

    # --- TABLE: RECENT ACTIVITY ---
    recent_bookings = Booking.objects.select_related('user', 'car').order_by('-created_at')[:5]

    context = {
        # KPI Stats
        "total_users": total_users,
        "total_cars": total_cars,
        "total_orders": total_orders,
        "total_amount": total_revenue,
        
        # Chart Data
        "rev_labels": booking_labels,
        "rev_values": earnings_data,
        "status_labels": status_labels,
        "status_values": status_values,
        "car_labels": car_labels,
        "car_values": car_values,
        
        # Table Data
        "recent_bookings": recent_bookings,
        "year": 2026,
    }

    return render(request, "admin_dashboard.html", context)
# -------------------- ADMIN ADD CAR --------------------
def add_car(request):

    if request.session.get("role") != "owner":
            return redirect("login")
    

    owner_id = request.session.get("owner_id")
    if not owner_id:
        return redirect("login")

    owner = get_object_or_404(Owner, id=owner_id)
    

    if request.method == "POST":

        # Strip spaces from text fields
        name = request.POST.get("name", "").strip()
        brand = request.POST.get("brand", "").strip()
        model = request.POST.get("model", "").strip()
        variant = request.POST.get("variant", "").strip()
        place = request.POST.get("place", "").strip()

        car_type = request.POST.get("car_type")
        fuel_type = request.POST.get("fuel_type")
        transmission = request.POST.get("transmission")
        seats = request.POST.get("seats")
        price = request.POST.get("price")

        image = request.FILES.get("image")

        # ❌ Validation
        if not all([name, brand, model, variant, place]):
            messages.error(request, "Text fields cannot be empty.")
            return render(request, "add_car.html")

        if not image:
            messages.error(request, "Car image is required.")
            return render(request, "add_car.html")

        if not image.content_type.startswith("image"):
            messages.error(request, "Only image files are allowed.")
            return render(request, "add_car.html")

        # ✅ Save
        Car.objects.create(
            name=name,
            brand=brand,
            model=model,
            variant=variant,
            place=place,
            car_type=car_type,
            fuel_type=fuel_type,
            transmission=transmission,
            seats=seats,
            price_per_hour=price,
            image=image,
            owner_id=owner_id
        )
        print("FILES:", request.FILES)
        print("IMAGE:", image)

        messages.success(request, "Car added successfully.")
        return redirect("add_car")

    return render(request, "owner/add_car.html")


def edit_car(request, car_id):


    if request.session.get("role") != "owner":
            return redirect("login")
    
    
    car = get_object_or_404(Car, id=car_id)

    owner_id = request.session.get("owner_id")
    if car.owner_id!=owner_id:
        return redirect("owner_dashboard")






    if request.method == "POST":
        car.name = request.POST.get("name")
        car.brand = request.POST.get("brand")
        car.model = request.POST.get("model")
        car.variant = request.POST.get("variant")
        car.place = request.POST.get("place")
        car.car_type = request.POST.get("car_type")
        car.fuel_type = request.POST.get("fuel_type")
        car.transmission = request.POST.get("transmission")
        car.seats = request.POST.get("seats")
        car.price_per_hour = request.POST.get("price")

        if request.FILES.get("image"):
            car.image = request.FILES.get("image")

        car.save()
        messages.success(request, "Car updated successfully")
        return redirect("owner_dashboard")

    return render(request, "owner/edit_car.html", {"car": car})


def toggle_car_status(request, car_id):
    if request.method == "POST":
        car = get_object_or_404(Car, id=car_id)

        car.available = not car.available
        car.save()

       


    messages.get_messages(request)

    return redirect("owner_dashboard")


def toggle_car_status_admin(request, car_id):
    if request.method == "POST":
        car = get_object_or_404(Car, id=car_id)

        car.available = not car.available
        car.save()

       


    messages.get_messages(request)

    return redirect("manage_cars")


# -------------------- USER management --------------------


def manage_users(request):
    users = User.objects.all().order_by("-id")
    return render(request, "manage_users.html", {"users": users})


def manage_cars(request):
    cars = Car.objects.all().order_by("-created_at")
    return render(request, "manage_cars.html", {"cars": cars})


def activate_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.isActive = True
    user.save()
    return redirect("manage_users")


def deactivate_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.isActive = False
    user.save()
    return redirect("manage_users")




# -------------------- USER CAR PAGE --------------------
def car_list(request):
    category = request.GET.get("category", None)
    if category:
        cars = Car.objects.filter(category=category)
    else:
        cars = Car.objects.all()
    return render(request, "car.html", {"cars": cars, "selected_category": category})


def location_suggestions(request):
    query = request.GET.get("q", "").strip()

    if not query:
        return JsonResponse({"results": []})

    places = (
        Car.objects.filter(place__icontains=query)
        .values_list("place", flat=True)
        .distinct()
        .order_by("place")
    )

    return JsonResponse({"results": list(places)})








def admin_bookings(request):
    if not request.session.get("admin_logged_in"):
        return redirect("admin_login")

    all_bookings = Booking.objects.select_related("user", "car").order_by("-id")

    return render(request, "admin_bookings.html", {"bookings": all_bookings})


def admin_delete_car(request, car_id):
    car = get_object_or_404(Car, id=car_id)
    car.delete()
    return redirect("admin_add_car")


def admin_edit_car(request, id):
    car = get_object_or_404(Car, id=id)

    if request.method == "POST":
        car.name = request.POST["name"]
        car.brand = request.POST["brand"]
        car.category = request.POST["category"]
        car.price_per_hour = request.POST["price_per_hour"]

        if "image" in request.FILES:
            car.image = request.FILES["image"]

        car.save()
        return redirect("admin_add_car")

    return render(request, "admin_edit_car.html", {"car": car})


def payment_report(request):
    bookings = Booking.objects.select_related("user", "car").order_by(
        "id"
    )  # ASCENDING ORDER

    total_revenue = bookings.aggregate(total=Sum("total_amount"))["total"] or 0

    return render(
        request,
        "admin_payment_list.html",
        {"bookings": bookings, "total_revenue": total_revenue},
    )


# -------------------- USER CAR search --------------------


def find_cars(request):

    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login")


    name = request.GET.get("name")
    pickup_location = request.GET.get("pickup")

    if name:
        cars=Car.objects.filter(available=True,name=name)
    else:   
    #  cars = Car.objects.filter(available=True,place=pickup_location) 
     cars = Car.objects.filter(available=True,place=pickup_location)
     

    pickup_date = request.GET.get("pickup_date")
    pickup_time = request.GET.get("pickup_time")
    drop_date = request.GET.get("drop_date")
    drop_time = request.GET.get("drop_time")

    pickup_dt = None
    drop_dt = None

    
     



    try:
        pickup_dt = datetime.strptime(
            f"{pickup_date} {pickup_time}", "%d %b %Y %I:%M %p"
        )
        drop_dt = datetime.strptime(f"{drop_date} {drop_time}", "%d %b %Y %I:%M %p")

    except Exception as e:
        print("Checkout error:", e)

    car_data = []

    for car in cars:
        is_time_available = True
        fav = Favourite.objects.filter(user_id=user_id, car_id=car.id)
        if fav:
            is_fav=True
        else:
            is_fav=False

        if pickup_dt and drop_dt:
            overlapping_booking = Booking.objects.filter(
                car=car, drop_datetime__gt=pickup_dt,payment_status="PAID",status__in=["BOOKED", "Running"]
            ).exists()

            if overlapping_booking:
                is_time_available = False


        car_data.append({"car": car, "is_time_available": is_time_available,"is_fav":is_fav})

    return render(request, "find_cars.html", {"car_data": car_data})


def checkout(request, car_id):

    
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login")
    
    
    car = get_object_or_404(Car, id=car_id)

    pickup = request.GET.get("pickup")
    drop = request.GET.get("drop") or pickup
    pickup_date = request.GET.get("pickup_date")
    pickup_time = request.GET.get("pickup_time")
    drop_date = request.GET.get("drop_date")
    drop_time = request.GET.get("drop_time")

    total_hours = 1
    total_price = car.price_per_hour


    want_driver = request.GET.get("want_driver") == "on"

    


    try:
     
        pickup_dt = datetime.strptime(
            f"{pickup_date} {pickup_time}", "%d %b %Y %I:%M %p"
        )
        drop_dt = datetime.strptime(f"{drop_date} {drop_time}", "%d %b %Y %I:%M %p")
        if pickup_dt and drop_dt:   
         conflict = Booking.objects.filter(
                car=car, drop_datetime__gt=pickup_dt, status="BOOKED"
            ).exists()


        if conflict:
            return HttpResponse("Car already booked for this time", status=409)

        duration_seconds = (drop_dt - pickup_dt).total_seconds()

        if duration_seconds <= 0:
            raise ValueError("Invalid time range")

        total_hours = max(1, math.ceil(duration_seconds / 3600))
        total_price = total_hours * car.price_per_hour

        driver_cost = 0

        if want_driver:
         driver_cost = 500 + (100 * total_hours)

         final_price = total_price + driver_cost

    except Exception as e:
        print("Checkout error:", e)

    context = {
        "car": car,
        "pickup": pickup,
        "drop": drop,
        "pickup_date": pickup_date,
        "pickup_time": pickup_time,
        "drop_date": drop_date,
        "drop_time": drop_time,
        "total_hours": total_hours,
        "total_price": final_price if want_driver else total_price,
    }

    return render(request, "checkout.html", context)




def confirm_pay(request, car_id):
    car = get_object_or_404(Car, id=car_id)
    user_id = request.session.get("user_id")
    
    if not user_id:
        return redirect("login")
    
    user = get_object_or_404(User, id=user_id)
    want_driver = request.GET.get("want_driver")

    # --- 1. HANDLE POST (Create NEW Booking) ---
    if request.method == "POST":
        # Delete ANY existing PENDING bookings for this specific user and car 
        # before creating a new one to prevent conflicts.
        Booking.objects.filter(user=user, car=car, payment_status="Pending").delete()


       

        if want_driver == "on":
          driver_status = True
        else:
         driver_status = False   # or "started" based on your flow

        pickup = request.GET.get("pickup")
        drop = request.GET.get("drop") or pickup
        pickup_date = request.GET.get("pickup_date")
        pickup_time = request.GET.get("pickup_time")
        drop_date = request.GET.get("drop_date")
        drop_time = request.GET.get("drop_time")
        

        try:
        

            
            pickup_dt = datetime.strptime(f"{pickup_date} {pickup_time}", "%d %b %Y %I:%M %p")
            drop_dt = datetime.strptime(f"{drop_date} {drop_time}", "%d %b %Y %I:%M %p")
            total_hours = math.ceil((drop_dt - pickup_dt).total_seconds() / 3600)
            total_price = total_hours * car.price_per_hour
            driver_cost = 0

            if want_driver == 'on':
             driver_cost = 500 + (100 * total_hours)
             total_price += driver_cost
            
        except:
             return redirect("index")

        # Create fresh Booking
        booking = Booking.objects.create(
            user=user,
            owner_id=car.owner_id,
            car=car,
            pickup_location=pickup,
            drop_location=drop,
            pickup_datetime=pickup_dt,
            drop_datetime=drop_dt,
            total_hours=total_hours,
            total_price=total_price,
            payment_status="PENDING",
            want_driver=driver_status,
            status="Pending",
        )

        # Create Razorpay Order
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        order_data = {
            "amount": int(total_price * 100),
            "currency": "INR",
            "payment_capture": 1,
        }
        order = client.order.create(order_data)

        booking.order_id = order["id"]
        booking.save()

        return redirect("confirm_pay", car_id=car.id)

    # --- 2. HANDLE GET (Show Details or Pay Button) ---
    
    # Capture URL Params to see if the user is changing dates
    pickup_date_param = request.GET.get("pickup_date")

    # If the user just came from the search page (URL has params),
    # we IGNORE existing pending bookings to show the NEW requested dates.
    if pickup_date_param:
        existing_booking = None
    else:
        existing_booking = Booking.objects.filter(
            user=user, 
            car=car,
            payment_status="PENDING",
        ).order_by('-id').first()

    order = None
    
    if existing_booking:
        # User has already clicked 'Confirm' and is on the payment step
        pickup = existing_booking.pickup_location
        drop = existing_booking.drop_location
        total_hours = existing_booking.total_hours
        total_price = existing_booking.total_price
        
        if existing_booking.order_id:
            order = {
                "id": existing_booking.order_id,
                "amount": int(existing_booking.total_price * 100)
            }
            
    else:
        # User is viewing the confirmation details for the FIRST time
        pickup = request.GET.get("pickup")
        drop = request.GET.get("drop") or pickup
        pickup_date = request.GET.get("pickup_date")
        pickup_time = request.GET.get("pickup_time")
        drop_date = request.GET.get("drop_date")
        drop_time = request.GET.get("drop_time")

        try:
            pickup_dt = datetime.strptime(f"{pickup_date} {pickup_time}", "%d %b %Y %I:%M %p")
            drop_dt = datetime.strptime(f"{drop_date} {drop_time}", "%d %b %Y %I:%M %p")

            if drop_dt <= pickup_dt: raise ValueError
            
            total_hours = math.ceil((drop_dt - pickup_dt).total_seconds() / 3600)
            total_price = total_hours * car.price_per_hour
            
            if want_driver == 'on':
             driver_cost = 500 + (100 * total_hours)
             total_price += driver_cost
        except Exception:
             return render(request, "confirm_pay.html", {
                "car": car, "error": "Invalid Dates"
            })

    return render(request, "confirm_pay.html", {
        "car": car,
        "pickup": pickup,
        "drop": drop,
        "total_hours": total_hours,
        "total_price": total_price,
        "order": order,
        "razorpay_key": settings.RAZORPAY_KEY_ID,
    })

@csrf_exempt
def payment_success(request):
    # ✅ CHANGE: Razorpay sends data via POST when using callback_url
    data = request.POST 


    # Verify keys exist (same as before)
    required_keys = [
        "razorpay_order_id",
        "razorpay_payment_id",
        "razorpay_signature",
    ]
    for key in required_keys:
        if key not in data:
            return HttpResponse(f"Missing {key}", status=400)

    client = razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )

    try:
        # Verify Payment
        client.utility.verify_payment_signature({
            "razorpay_order_id": data["razorpay_order_id"],
            "razorpay_payment_id": data["razorpay_payment_id"],
            "razorpay_signature": data["razorpay_signature"],
        })

        booking = Booking.objects.get(order_id=data["razorpay_order_id"])
        user=User.objects.get(id=booking.user_id)
        
        booking.payment_status = "PAID"

        if booking.want_driver:
         booking.status = "Pending"
        else:
         booking.status = "booked"
        
        booking.save()

        twiloclient = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)




        message = (
            f"Hi {user.username}, 👋\n\n"
            f"Your booking is successfully confirmed! ✅\n"
            f"Booking ID: {booking.id}\n\n"
            f"Please reach the pickup location on time. "
            f"You will receive another message when your car is ready. 🚗"
        )

        twiloclient.messages.create(
            body=message,
            from_=settings.TWILIO_PHONE_NUMBER,
            to="+91" +str(user.phonenumber)
        )


        

        return redirect("booking_success",id=booking.id)

    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=500)



def booking_success(request, id):
    # 1. Get the user ID from your custom session
    user_id = request.session.get("user_id")
    
    # 2. If no user_id in session, send them to login
    if not user_id:
        return redirect("login")
    
    # 3. Fetch the booking using the numeric user_id, NOT request.user
    booking = get_object_or_404(Booking, id=id, user_id=user_id)
    owner = get_object_or_404(Owner, id=booking.owner_id)

    

    return render(request, "order_confirmation.html", {"booking": booking ,"owner":owner})

def name_suggestions(request):
    q = request.GET.get("q", "")
    names = (
        Car.objects.filter(name__icontains=q)
        .values_list("name", flat=True)
        .distinct()
    )
    return JsonResponse({"results": list(names)})




def profile(request):
    # 🔐 Get logged-in user from session
    user_id = request.session.get("user_id")

    if not user_id:
        return redirect("login")

    user = User.objects.get(id=user_id)

    now = timezone.now()

    active_bookings = Booking.objects.filter(
        user_id=user,
        status__in=["BOOKED","Running","Pending"]
    ).order_by("pickup_datetime")

    completed_bookings = Booking.objects.filter(
    user_id=user,
    status__in=["COMPLETED", "CANCELLED"]
     ).order_by("-drop_datetime")


    return render(request, "profile.html", {
        "user": user,
        "active_bookings": active_bookings,
        "completed_bookings": completed_bookings
    })



def booking_detail(request, booking_id):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login")

    user = User.objects.get(id=user_id)
    

    booking = get_object_or_404(
        Booking,
        id=booking_id,
        user_id=user
    )


    owner = get_object_or_404(
        Owner,
        id=booking.owner_id, 
    )

    

    now = timezone.now()

    is_active = (booking.status == "BOOKED")

    try:
        user_review = Review.objects.get(booking=booking)
    except Review.DoesNotExist:
        user_review = None



    messages = ChatMessage.objects.filter(
        booking=booking
    ).order_by('timestamp')    

    return render(request, "booking_detail.html", {
        "booking": booking,
        'user_review': user_review,
        "owner":owner,
        "is_active": is_active,
        "chatmessages": messages
    })



def cancel_booking(request, booking_id):
    user_id = request.session.get("user_id")

    if not user_id:
        return redirect("login")

    user = User.objects.get(id=user_id)


    booking = get_object_or_404(
        Booking,
        id=booking_id,
        user_id=user_id
    )

    if booking.drop_datetime > timezone.now():
        booking.status = "CANCELLED"
        booking.payment_status = "REFUNDED"
        booking.save()

    return redirect("profile")




def admin_orders(request):
    # ✅ simple admin session check
    if request.session.get("role") != "admin":
        return redirect("login")

    now = timezone.now()

    bookings = Booking.objects.all().order_by("-created_at")

    # Auto-complete finished trips
    for booking in bookings:
        if booking.status == "BOOKED" and booking.drop_datetime < now:
            booking.status = "COMPLETED"
            booking.save()

    return render(request, "admin_orders.html", {
        "bookings": bookings
    })



def admin_cancel_booking(request, booking_id):
    if request.session.get("role") != "admin":
        return redirect("login")

    booking = get_object_or_404(Booking, id=booking_id)

    if booking.status == "BOOKED":
        booking.status = "CANCELLED"
        booking.payment_status = "REFUNDED"
        booking.save()

    return redirect("admin_orders")


def admin_revenue(request):
    completed_bookings = Booking.objects.filter(status="COMPLETED")
    current_bookings = Booking.objects.filter(status="BOOKED")
    cancelled_bookings = Booking.objects.filter(status="CANCELLED")

    completed_revenue = completed_bookings.aggregate(
        total=Sum("total_price")
    )["total"] or 0
    upcoming_revenue = current_bookings.aggregate(
        total=Sum("total_price")
    )["total"] or 0

    cancelled_amount = cancelled_bookings.aggregate(
        total=Sum("total_price")
    )["total"] or 0

    total_revenue = completed_revenue  # business rule: onfly completed counts

    return render(request, "revenue.html", {
        "completed_revenue": completed_revenue,
        "cancelled_amount": cancelled_amount,
        "total_revenue": total_revenue,
        "completed_bookings": completed_bookings,
        'upcoming_revenue': upcoming_revenue

    })


def owner_cancel_booking(request, booking_id):


    if request.session.get("role") != "owner":
        return redirect("ownr")
    # 1. Get logged-in user ID
    owner_id = request.session.get("owner_id")
    if not owner_id:
        return redirect("own")

    # 2. Fetch the booking
    booking = get_object_or_404(Booking, id=booking_id)

    # 3. SECURITY CHECK: Ensure the logged-in user is the OWNER of the car
    # We compare the session user_id with the car's owner_id
    if booking.owner_id != owner_id:
        # If they aren't the owner, deny access (or redirect home)
        return redirect("hughgh")

    # 4. Update Status
    booking.status = "CANCELLED"
    booking.payment_status = "REFUNDED"
    booking.save()

    # 5. Redirect back to the Owner Dashboard
    return redirect("owner_dashboard")





def toggle_favourite(request, car_id):


    if request.method == 'POST':

      user_id = request.session.get("user_id")
      if not user_id:
        return redirect("login")
    
      try:
            
            favourite, created = Favourite.objects.get_or_create(user_id=user_id, car_id=car_id)
            if not created:
                favourite.delete()
                return JsonResponse({'status': 'removed'})
            return JsonResponse({'status': 'added'})
      except Car.DoesNotExist:
            return JsonResponse({'error': 'Car not found'}, status=404)
    return JsonResponse({'error': 'Invalid request'}, status=400)




def favourites_view(request):


    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login")
    # Get all cars where the current user is in the favourites list
    fav_items = Favourite.objects.filter(user_id=user_id).select_related('car')
    
    return render(request, 'favourites.html', {
        'favourites': fav_items
    })



def submit_review(request, booking_id):
    if request.method == "POST":
        # 1. Get the booking and verify ownership
        booking = get_object_or_404(Booking, id=booking_id)

        user_id=request.session.get("user_id")
        if not user_id:
            return redirect("login")
        
        # Security check: Ensure the logged-in user owns this booking
        if booking.user_id != user_id:
            messages.error(request, "You are not authorized to review this booking.")
            return redirect('index')

        # 2. Get data from form
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')

        # 3. Create the review
        try:
            Review.objects.create(
                booking_id=booking_id,
                car_id=booking.car_id,
                user_id=user_id,
                rating=rating,
                comment=comment
            )
            messages.success(request, "Thank you! Your review has been submitted.")
        except Exception as e:
            messages.error(request, "Error submitting review. You may have already reviewed this.")
            
        # 4. Redirect back to the details page
        return redirect('booking_detail', booking_id=booking.id)

    return redirect('index')



def delete_review(request, review_id):

    user_id=request.session.get("user_id")
    if not user_id:
            return redirect("login")
    
    review = get_object_or_404(Review, id=review_id)
    
    # Security Check
    if user_id == review.user_id:
        review.delete()
        return JsonResponse({'status': 'success', 'message': 'Review deleted successfully'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)





def forgot_password(request):
    if request.method == "POST":
        email = request.POST.get("email")

        # Check if user exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "No account found with this email.")
            return render(request, "forgot_password.html")

        # Generate 6-digit OTP
        otp = str(random.randint(100000, 999999))

        # Store in session
        request.session['otp'] = otp
        request.session['reset_email'] = email
        
        # Send Email
        subject = "Your Password Reset OTP"
        message = f"Hello {user.username},\n\nYour OTP for password reset is: {otp}\n\nDo not share this with anyone."
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [email]
        
        try:
            send_mail(subject, message, from_email, recipient_list)
            messages.success(request, "OTP sent to your email.")
            return redirect("verifyforget_otp")
        except Exception as e:
            messages.error(request, f"Failed to send email: {e}")
            return redirect("forgot_password")

    return render(request, "forgot_password.html")


def verifyforget_otp(request):
    if request.method == "POST":
        entered_otp = request.POST.get("otp")
        session_otp = request.session.get("otp")

        if entered_otp == session_otp:
            # Mark as verified in session so they can access reset page
            request.session['otp_verified'] = True
            messages.success(request, "OTP Verified.")
            return redirect("reset_password")
        else:
            messages.error(request, "Invalid OTP. Please try again.")

    return render(request, "verify_forgetotp.html")


def reset_password(request):
    # Security check: User must have verified OTP
    if not request.session.get("otp_verified") or not request.session.get("reset_email"):
        messages.error(request, "Unauthorized access. Please start over.")
        return redirect("forgot_password")

    if request.method == "POST":
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        if new_password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, "reset_password.html")

        email = request.session.get("reset_email")
        
        try:
            user = User.objects.get(email=email)
            user.password = make_password(new_password) # Hashes the password automatically
            user.save()
            
            # Clean up session
            del request.session['otp']
            del request.session['reset_email']
            del request.session['otp_verified']

            messages.success(request, "Password reset successful. Please login.")
            return redirect("login")
            
        except User.DoesNotExist:
            messages.error(request, "User not found.")
            return redirect("forgot_password")

    return render(request, "reset_password.html")



# views.py
def all_cars(request):
    # Fetch all cars (or all active cars)
    cars = Car.objects.all().order_by('-id') 
    return render(request, 'all_cars.html', {'cars': cars})



def owner_order_detail(request, booking_id):
    # 1. Security Check: Ensure user is Owner
    if request.session.get("role") != "owner":
        messages.error(request, "Unauthorized access.")
        return redirect("login")

    # 2. Fetch the Booking
    booking = get_object_or_404(Booking, id=booking_id)

    # 3. Fetch Review if it exists for this booking
    #    (Using .first() prevents errors if multiple reviews accidentally exist)
    review = Review.objects.filter(booking=booking).first()

    context = {
        'booking': booking,
        'review': review,
    }
    return render(request, 'owner/order_detail.html', context)



def admin_order_detail(request, booking_id):
    # 1. Security Check
    if request.session.get("role") != "admin":
        return redirect("login")

    # 2. Fetch Booking
    booking = get_object_or_404(Booking, id=booking_id)

    # 3. Fetch Review (if it exists)
    review = Review.objects.filter(booking=booking).first()

    context = {
        "booking": booking,
        "review": review,
    }
    return render(request, "admin_order_details.html", context)





def owner_car_detail(request, car_id):
    car = get_object_or_404(Car, id=car_id)
    now = timezone.now()

    # 1. Current Booking: Trip is currently happening
    current_booking = Booking.objects.filter(
        car_id=car_id, 
        status__in=[ 'Running'],
        
    ).first()

    # 2. Next Bookings: All future trips, excluding the one currently happening
    # We order by pickup_datetime so the "soonest" trip is first
    next_bookings = Booking.objects.filter(
    car_id=car_id, 
    status__in=['BOOKED', 'Pending', 'Ready for Pickup'] # Correct way to use "OR" logic
   ).order_by('pickup_datetime')

    reviews = Review.objects.filter(car=car).order_by('-created_at')
    
    return render(request, 'owner/car_detail_view.html', {
        'car': car,
        'current_booking': current_booking,
        'next_bookings': next_bookings,
        'reviews': reviews
    })




def booking_action(request, booking_id, action):
    booking = get_object_or_404(Booking, id=booking_id)
    car= get_object_or_404(Car, id=booking.car_id)
    user_phone = booking.user.phonenumber # Ensure you have a phone field
    
    # Twilio Client Setup
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    
    if action == "drop_alert":
        msg_body = f"URGENT: Your rental for {booking.car.name} ends in 10 mins. Please reach the drop-off point to avoid late fees!"
        
        # Send SMS via Twilio
        client.messages.create(
            body=msg_body,
            from_=settings.TWILIO_PHONE_NUMBER,
            to="+91" + str(user_phone)
        )
        messages.warning(request, "10-minute SMS alert sent to driver.")
        
    elif action == "ready":
        msg_body = f"Good news! Your RoyalRental ({booking.car.name}) is clean, fueled, and ready for pickup."
        client.messages.create(
            body=msg_body,
            from_=settings.TWILIO_PHONE_NUMBER,
            to="+91" + str(user_phone)
        )
        booking.status = "Ready for Pickup"
        booking.save()
        messages.success(request, "Pickup notification sent via SMS.")


    elif action == "started":
    # 1. Update the booking status to indicate the trip is active
     booking.status = "Running"  # Or "STARTED" based on your preference
     booking.save()

     drop_time = timezone.localtime(booking.drop_datetime)

    # 2. Prepare the Trip Start Message
     msg_body = (
     f"Trip Started! You have successfully picked up your RoyalRental ({booking.car.name}). "
     f"Please drive safely! Your scheduled return time is {drop_time.strftime('%d %b, %I:%M %p')}."
        )

    # 3. Send Twilio SMS
     client.messages.create(
            body=msg_body,
            from_=settings.TWILIO_PHONE_NUMBER,
            to="+91" + str(booking.user.phonenumber)
        )
     messages.success(request, f"Trip for {booking.car.name} has officially started.")
     

    elif action == "completed":
        msg_body = (
        f"Thank you for choosing RoyalRentals! Your trip with {booking.car.name} "
        f"is now officially closed. We hope you had a great drive!"
    )
        client.messages.create(
            body=msg_body,
            from_=settings.TWILIO_PHONE_NUMBER,
            to="+91" + str(booking.user.phonenumber)
        )

        booking.status = "COMPLETED"
        booking.save()
        
        messages.success(request, "Trip completed notification sent via SMS.")   

    return redirect('owner_car_detail', car_id=booking.car.id)



    
def driver_register(request):
    messages.get_messages(request)

    # 🔐 Role-based redirects
    if request.session.get("role") == "admin":
        return redirect("admin_dashboard")

    if request.session.get("role") == "customer":
        return redirect("index")

    if request.session.get("role") == "owner":
        return redirect("owner_dashboard")

    if request.session.get("role") == "driver":
        return redirect("driver_dashboard")

    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        # 🆕 Driver-specific fields
        license_number = request.POST.get("license_number")
        license_expiry = request.POST.get("license_expiry")
        experience_years = request.POST.get("experience_years")

        # ✅ Password check
        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return redirect("driver_register")

        # ✅ Unique checks
        if Driver.objects.filter(phone=phone).exists():
            messages.error(request, "Driver already registered with this phone")
            return redirect("driver_register")

        if Driver.objects.filter(email=email).exists():
            messages.error(request, "Email already exists")
            return redirect("driver_register")

        if Driver.objects.filter(license_number=license_number).exists():
            messages.error(request, "License already registered")
            return redirect("driver_register")

        # 🚗 Create Driver (inactive)
        driver = Driver.objects.create(
            name=name,
            email=email,
            phone=phone,
            license_number=license_number,
            license_expiry=license_expiry if license_expiry else None,
            experience_years=experience_years or 0,
            is_available=False,
            isActive=True,
            status="online"
        )

        driver.set_password(password)
        driver.save()

        

        return redirect("verify_driver_otp", phone=phone)

    return render(request, "driver/register.html")


def driver_login(request):
    messages.get_messages(request)

    # 🔐 Role redirects
    if request.session.get("role") == "admin":
        return redirect("admin_dashboard")

    if request.session.get("role") == "customer":
        return redirect("index")

    if request.session.get("role") == "owner":
        return redirect("owner_dashboard")

    if request.session.get("role") == "driver":
        return redirect("driver_dashboard")

    # 🔑 LOGIN LOGIC
    if request.method == "POST":
        phone = request.POST.get("phone")
        password = request.POST.get("password")

        try:
            driver = Driver.objects.get(phone=phone)

            # 🚫 Check if verified
            if not driver.isActive:
                messages.error(request, "Account is disabled")
                return render(request, "driver/login.html")

            # 🔐 Password check
            if driver.check_password(password):
                request.session.flush()

                request.session["driver_id"] = driver.id
                request.session["username"] = driver.name
                request.session["role"] = "driver"

                return redirect("driver_dashboard")
            else:
                messages.error(request, "Invalid password")
                return render(request, "driver/login.html")

        except Driver.DoesNotExist:
            messages.error(request, "Driver not found")
            return render(request, "driver/login.html")

    return render(request, "driver/login.html")




def driver_dashboard(request):

    if request.session.get("role") != "driver":
        return redirect("driver_login")

    driver_id = request.session.get("driver_id")

    driver = Driver.objects.get(id=driver_id)


    pending_requests = Booking.objects.filter(status='Pending').order_by('-created_at')

    upcoming_trips = Booking.objects.filter(
        driver_id=driver_id,
        status='BOOKED'
    )

    ongoing_trips = Booking.objects.filter(
        driver_id=driver_id,
        status='Running'
    )

    completed_trips = Booking.objects.filter(
        driver_id=driver_id,
        status='COMPLETED'
    )

    cancelled_trips = Booking.objects.filter(
        driver_id=driver_id,
        status='CANCELLED'
    )

    history=Booking.objects.filter(
        driver_id=driver_id,    
    )

    

    total_earnings = (
        Booking.objects
        .filter(driver_id=driver_id, status="COMPLETED")
        .aggregate(total=Sum("total_price"))
        .get("total") or 0
    )
    driver_bookings = Booking.objects.filter(
    driver_id=driver_id,
    status__in=["BOOKED", "Running"]
     )
    messages = ChatMessage.objects.filter(
    booking__in=driver_bookings
     ).order_by('timestamp')

    total_trips = completed_trips.count()

    avg_per_trip = total_earnings / total_trips if total_trips > 0 else 0

    
    today = localdate()
    today_earnings = (
       Booking.objects
        .filter(
         driver_id=driver_id,
         status="COMPLETED",
         pickup_datetime__date=today
        )
       .aggregate(total=Sum("total_price"))
       .get("total") or 0
     )
    
    last_7_days = localdate() - timedelta(days=6)



    chart_data = (
    Booking.objects
    .filter(
        driver_id=driver_id,
        status="COMPLETED",
        pickup_datetime__date__gte=last_7_days
    )
    .annotate(day=TruncDate("pickup_datetime"))
    .values("day")
    .annotate(total=Sum("total_price"))
    .order_by("day")
)
    chart_days = []
    chart_totals = []

    for i in range(7):
     day = last_7_days + timedelta(days=i)
     chart_days.append(day.strftime("%d %b"))

     total = next(
        (x["total"] for x in chart_data if str(x["day"]) == str(day)),
        0
     )
     chart_totals.append(total)


    context = {
    "driver": driver,
    "pending_requests": pending_requests,
    "upcoming_trips": upcoming_trips,
    "ongoing_trips": ongoing_trips,
    "completed_trips": completed_trips,
    "cancelled_trips": cancelled_trips,
    "history": history,

    # earnings
    "total_earnings": total_earnings,
    "today_earnings": today_earnings,
    "avg_per_trip": avg_per_trip,
    "total_trips": total_trips,

    # chart
    "chart_days": json.dumps(chart_days),
    "chart_totals": json.dumps(chart_totals),

    "messages": messages,
    "driver_bookings": driver_bookings,
}

    return render(request, "driver/dashboard.html", context)



def accept_request(request, booking_id):

    if request.session.get("role") != "driver":
        return redirect("driver_login")

    driver_id = request.session.get("driver_id")

    booking = get_object_or_404(Booking, id=booking_id)

    # ✅ Only allow accepting pending driver requests
    if booking.status == "Pending" and booking.want_driver:

        booking.driver_id = driver_id
        booking.status = "BOOKED"
        booking.save()

    return redirect("driver_dashboard")



def cancel_request(request, booking_id):

    if request.session.get("role") != "driver":
        return redirect("driver_login")

    driver_id = request.session.get("driver_id")
    if not driver_id:
        return redirect("driver_login")

    driver = Driver.objects.get(id=driver_id)

    booking = get_object_or_404(Booking, id=booking_id, driver=driver)

    # ✅ Only allow cancel if driver had accepted
    if booking.status == "BOOKED" and booking.want_driver:

        booking.driver = None   # ✅ FIXED (no comma)
        booking.status = "Pending"  # ✅ lowercase

        booking.save()

    return redirect("driver_dashboard")



def driver_list(request):
    drivers = Driver.objects.all()
    return render(request, 'driver-details.html', {'drivers': drivers})


def activate_driver(request, id):
    driver = Driver.objects.get(id=id)
    driver.isActive = True
    driver.save()
    return redirect('driver_list')


def deactivate_driver(request, id):
    driver = Driver.objects.get(id=id)
    driver.isActive = False
    driver.save()
    return redirect('driver_list')


def delete_driver(request, id):
    driver = Driver.objects.get(id=id)
    driver.delete()
    return redirect('driver_list')




def chat_view(request, booking_id):
    booking = Booking.objects.get(id=booking_id)

    messages = ChatMessage.objects.filter(
        booking=booking
    ).order_by('timestamp')

    if request.method == "POST":
        if request.session.get("role") == "driver":

            ChatMessage.objects.create(
                booking=booking,
                sender_id=request.session['driver_id'],
                sender_type="driver",
                receiver_id=booking.user_id,
                receiver_type="user",
                message=request.POST['message']
            )
            return redirect('driver_dashboard')

        else:
            ChatMessage.objects.create(
                booking=booking,
                sender_id=request.session['user_id'],
                sender_type="user",
                receiver_id=booking.driver_id,
                receiver_type="driver",
                message=request.POST['message']
            )
            return redirect('booking_detail', booking_id=booking_id)

       

    return render(request, "chat.html", {
        "messages": messages,
        "booking": booking
    })

        




