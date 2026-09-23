from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views
from .views import CustomLoginView

urlpatterns = [
    path(
        'change-password/',
        auth_views.PasswordChangeView.as_view(
            template_name='registration/change_password.html',
            success_url=reverse_lazy('password_change_done')
        ),
        name='change_password'
    ),
    path(
        'change-password/done/',
        auth_views.PasswordChangeDoneView.as_view(
            template_name='registration/change_password_done.html'
        ),
        name='password_change_done'
    ),
    path('register/', views.register, name='register'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('custom-admin/', views.admin_booking_list_view, name='admin_booking_list'),
    path('custom-admin/booking-list/', views.admin_booking_list_view, name='admin_booking_list'),
    path('custom-admin/booking-list/add/', views.admin_add_booking_view, name='admin_add_booking'),
    path('custom-admin/booking-list/cancel/<int:booking_id>/', views.admin_cancel_booking_view, name='admin_cancel_booking'),
    path('custom-admin/booking-list/edit/<int:booking_id>/', views.admin_edit_booking_view, name='admin_edit_booking'),
    path('custom-admin/doctor/', views.admin_doctor_list_view, name='admin_doctor_list'),
    path('custom-admin/doctor/add/', views.admin_add_doctor_view, name='admin_add_doctor'),
    path('custom-admin/doctor/delete/<int:doctor_id>/', views.admin_delete_doctor_view, name='admin_delete_doctor'),
    path('custom-admin/doctor/edit/<int:doctor_id>/', views.admin_edit_doctor_view, name='admin_edit_doctor'),
    path('custom-admin/slot/', views.admin_slot_list_view, name='admin_slot_list'),
    path('custom-admin/slot/add/', views.admin_add_slot_view, name='admin_add_slot'),
    path('custom-admin/slot/edit/<int:slot_id>/', views.admin_edit_slot_view, name='admin_edit_slot'),
    path('custom-admin/slot/delete/<int:slot_id>/', views.admin_delete_slot_view, name='admin_delete_slot'),
    path('custom-admin/user-list/', views.admin_user_list_view, name='admin_user_list'),
    path('custom-admin/create-user/', views.admin_create_user_view, name='admin_create_user'),
    path('custom-admin/edit-user/<int:user_id>/', views.admin_edit_user_view, name='admin_edit_user'),
    path('custom-admin/suspend-user/<int:user_id>/', views.admin_suspend_user_view, name='admin_suspend_user'),
    path('custom-admin/active-user/<int:user_id>/', views.admin_active_user_view, name='admin_active_user'),
    path('custom-admin/delete-user/<int:user_id>/', views.admin_delete_user_view, name='admin_delete_user'),
    path('patient/booking-list/', views.patient_book_list_view, name='patient_book_list'),
    path('patient/booking-list/edit/<int:booking_id>/', views.patent_edit_booking_view, name='patient_edit_booking'),
    path('patient/booking-list/cancel/<int:booking_id>/', views.patient_cancel_booking_view, name='patient_cancel_booking'),
    path('patient/available-slots/', views.patient_available_slots_view, name='patient_available_slots'),
    path('patient/book-slot/<int:slot_id>/', views.patient_book_slot_direct_view, name='patient_book_slot_direct'),
    path('doctor/dashboard/', views.doctor_dashboard_view, name='doctor_dashboard'),
    path('booking/<int:booking_id>/add-comment/', views.doctor_add_comment_view, name='doctor_add_comment'),


]

