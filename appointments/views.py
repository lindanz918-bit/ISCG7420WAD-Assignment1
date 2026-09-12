from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test

from .forms import DoctorForm
from .models import Doctor, AppointmentSlot, Booking

# Helper check for admin users
def is_admin(user):
    return user.is_staff or user.is_superuser

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'

    def get_success_url(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return '/custom-admin/'
        return '/book/'

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Auto log-in after registration
            return redirect('book_appointment')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


# Book Appointment View
@login_required
def book_appointment(request):
    if request.method == 'POST':
        slot_id = request.POST.get('slot_id')
        slot = get_object_or_404(AppointmentSlot, id=slot_id, is_booked=False)

        Booking.objects.create(patient=request.user, slot=slot)
        slot.is_booked = True
        slot.save()

        return redirect('my_bookings')
    ## Show available unbooked slots (GET request)
    slots = AppointmentSlot.objects.filter(is_booked=False).select_related('doctor')
    return render(request, 'appointments/book.html', {'slots': slots})

# Custom Admin Dashboard View
@user_passes_test(is_admin)
def custom_admin_dashboard(request):
    doctors = Doctor.objects.all()
    bookings = Booking.objects.all().select_related('patient', 'slot__doctor')
    slots = AppointmentSlot.objects.all().select_related('doctor')
    return render(request, 'appointments/admin_dashboard.html', {
        'doctors': doctors,
        'bookings': bookings,
        'slots': slots,
    })

# Add Doctor
@user_passes_test(is_admin)
def add_doctor(request):
    if request.method == 'POST':
        form = DoctorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_dashboard')
    else:
        form = DoctorForm()
    return render(request, 'appointments/doctor_form.html', {'form': form})

@user_passes_test(is_admin)
def delete_doctor(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id)
    if request.method == 'POST':
        doctor.delete()
    return redirect('admin_dashboard')

@user_passes_test(is_admin)
def edit_doctor(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id)
    if request.method == 'POST':
        form = DoctorForm(request.POST, instance=doctor)
        if form.is_valid():
            form.save()
            return redirect('admin_dashboard')
    else:
        form = DoctorForm(instance=doctor)
    return render(request, 'appointments/doctor_form.html', {'form': form, 'title': 'Edit Doctor'})


