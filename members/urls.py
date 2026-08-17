from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),




    path('driver/register/', views.driver_register, name='driver_register'),
    path('driver/login/', views.driver_login, name='driver_login'),
    path('driver/dashboard/', views.driver_dashboard, name='driver_dashboard'),
    path('driver/accept/<int:booking_id>/', views.accept_request, name='accept_request'),
    path('driver/cancel/<int:booking_id>/', views.cancel_request, name='cancel_request'),
    

    
   



    path("owner/register/", views.owner_register, name="owner_register"),
    path("owner/login/", views.owner_login, name="owner_login"),
    path("owner/verify-otp/<str:phone>/", views.verify_owner_otp, name="verify_owner_otp"),
    path("owner/resend-otp/<str:phone>/",views.resend_owner_otp,name="resend_owner_otp"),
    path("owner/dashboard/", views.owner_dashboard, name="owner_dashboard"),
    path('owner/add-car/',  views.add_car, name="add_car"),
    path("owner/editcar/<int:car_id>/", views.edit_car, name="edit_car"),
    path("owner/car/disable/<int:car_id>/", views.toggle_car_status, name="disable_car"),
    path('owner/cancel-booking/<int:booking_id>/', views.owner_cancel_booking, name='owner_cancel_booking'),
    path('owner/order/<int:booking_id>/', views.owner_order_detail, name='owner_order_detail'),
    path('owner/car/<int:car_id>/', views.owner_car_detail, name='owner_car_detail'),
    path('owner/car/action/<int:booking_id>/<str:action>/', views.booking_action, name='booking_action'),



  
   

    path('register/', views.register, name='register'),
    path('verify_otp/', views.verify_otp, name='verify_otp'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('verify-forget-otp/', views.verifyforget_otp, name='verifyforget_otp'),
    path('reset-password/', views.reset_password, name='reset_password'),
 
    path('car/list/', views.car_list, name='car_list'),
    path("api/locations/", views.location_suggestions, name="location_suggestions"),
    path("find-cars/", views.find_cars, name="find_cars"),
    path('checkout/<int:car_id>/', views.checkout, name='checkout'),
    path("confirm-pay/<int:car_id>/", views.confirm_pay, name="confirm_pay"),
    path("payment-success/", views.payment_success, name="payment_success"),
    path('booking-success/<int:id>/', views.booking_success, name='booking_success'),
    path("profile/", views.profile, name="profile"),
    path("booking/<int:booking_id>/", views.booking_detail, name="booking_detail"),
    path("booking/<int:booking_id>/cancel/", views.cancel_booking, name="cancel_booking"),
    path('toggle-favourite/<int:car_id>/', views.toggle_favourite, name='toggle_favourite'),
    path('favourites/', views.favourites_view, name='favourites'),
    path('submit-review/<int:booking_id>/', views.submit_review, name='submit_review'),
    path('delete-review/<int:review_id>/', views.delete_review, name='delete_review'),
    path("name-suggestions/", views.name_suggestions, name="name_suggestions"),
    path('all-cars/', views.all_cars, name='all_cars'),
   




    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path("admin/orders/", views.admin_orders, name="admin_orders"),
    path("admin/orders/<int:booking_id>/cancel/", views.admin_cancel_booking, name="admin_cancel_booking"),
    path('admin/manage_cars/', views.manage_cars, name='manage_cars'),
    path('admin/users/', views.manage_users, name='manage_users'),
    path('admin/drivers/', views.driver_list, name='driver_list'),
    path('admin/drivers/activate/<int:id>/', views.activate_driver, name='activate_driver'),
    path('admin/drivers/deactivate/<int:id>/', views.deactivate_driver, name='deactivate_driver'),
    path('admin/drivers/delete/<int:id>/', views.delete_driver, name='delete_driver'),
    path('admin/users/activate/<int:user_id>/', views.activate_user, name='activate_user'),
    path('admin/users/deactivate/<int:user_id>/', views.deactivate_user, name='deactivate_user'),
    path("admin/car/disable/<int:car_id>/", views.toggle_car_status_admin, name="disable_car_admin"),
    path('admin/edit-car/<int:id>/', views.admin_edit_car, name='admin_edit_car'),
    path("admin/revenue/", views.admin_revenue, name="admin_revenue"),
    path('admin/delete_car/<int:car_id>/', views.admin_delete_car, name='admin_delete_car'),
    path("admin-bookings/", views.admin_bookings, name="admin_bookings"),
    path('admin-orders/<int:booking_id>/', views.admin_order_detail, name='admin_order_detail'),

   
 
 # 💬 Chat page (open conversation for a booking)
    path('chat/<int:booking_id>/', views.chat_view, name='chat_view'),



    
   
]
