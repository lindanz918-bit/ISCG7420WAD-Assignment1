

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.views.generic.dates import timezone_today

from .forms import DoctorForm, SlotForm, CustomUserCreateForm, EditUserForm, PatientEditBookingForm
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
        return '/patient/booking-list/'

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
@user_passes_test(is_admin)
def admin_booking_list_view(request):
    bookings = Booking.objects.all().select_related('patient', 'slot__doctor')
    now_local = timezone.localtime()
    return render(request, 'appointments/admin_booking_list.html', {
        'bookings': bookings,
        'today_date': now_local.date(),
        'current_time': now_local.time(),
        'search_query': request.GET.get('q', '')
    })


@user_passes_test(is_admin)
def admin_add_booking_view(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        slot_id = request.POST.get('slot_id')

        user = get_object_or_404(User, id=user_id)
        now_local = timezone.localtime()

        # Correct OR logic for validating slot expiration in POST
        future_slots = Q(date__gt=now_local.date()) | Q(date=now_local.date(), time__gte=now_local.time())

        slot = get_object_or_404(
            AppointmentSlot,
            id=slot_id,
            is_booked=False,
            *([future_slots])
        )

        Booking.objects.create(patient=user, slot=slot)
        slot.is_booked = True
        slot.save()

        messages.success(request, f"New booking for {user.username} added!")
        return redirect('admin_booking_list')

    # GET Request
    users = User.objects.all()
    doctors = Doctor.objects.all()

    selected_doctor_id = request.GET.get('doctor_id')
    slots = []
    if selected_doctor_id:
        now_local = timezone.localtime()
        # FIXED: Use date__gt for future days OR date=today with time >= now
        future_slots = Q(date__gt=now_local.date()) | Q(date=now_local.date(), time__gte=now_local.time())

        slots = AppointmentSlot.objects.filter(
            is_booked=False,
            doctor_id=selected_doctor_id
        ).filter(future_slots).select_related('doctor').order_by('date', 'time')

    context = {
        'users': users,
        'doctors': doctors,
        'slots': slots,
        'selected_doctor_id': selected_doctor_id,
    }
    return render(request, 'appointments/admin_add_booking.html', context)
@user_passes_test(is_admin)
def admin_edit_booking_view(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if request.method == 'POST':
        slot_id = request.POST.get('slot_id')
        if not slot_id:
            return redirect('admin_edit_booking', booking_id=booking.id)

        new_slot_id = int(slot_id)

        # Only update database models if the slot actually changed
        if new_slot_id != booking.slot.id:
            now_local = timezone.localtime()
            future_slot = Q(date__gt=now_local.date()) | Q(date=now_local.date(), time__gte=now_local.time())

            # Free up old slot
            old_slot = booking.slot
            old_slot.is_booked = False
            old_slot.save()

            # Ensure the newly chosen slot is unbooked AND not in the past
            new_slot = get_object_or_404(
                AppointmentSlot,
                future_slot,
                id=new_slot_id,
                is_booked=False
            )
            new_slot.is_booked = True
            new_slot.save()

            booking.slot = new_slot
            booking.save()

        messages.success(request, "Booking updated successfully!")
        return redirect('admin_booking_list')

    # GET Request Processing
    users = User.objects.all()
    doctors = Doctor.objects.all()

    selected_doctor_id = request.GET.get('doctor_id')
    if not selected_doctor_id:
        selected_doctor_id = str(booking.slot.doctor.id)

    now_local = timezone.localtime()
    # Use time__gte (greater than or equal to)
    future_slot = Q(date__gt=now_local.date()) | Q(date=now_local.date(), time__gte=now_local.time())

    # Include available future slots OR the slot currently assigned to this booking
    slots = AppointmentSlot.objects.filter(
        doctor_id=selected_doctor_id
    ).filter(
        (Q(is_booked=False) & future_slot) | Q(id=booking.slot.id)
    ).select_related('doctor').order_by('date', 'time')

    context = {
        'booking': booking,
        'users': users,
        'doctors': doctors,
        'slots': slots,
        'selected_doctor_id': selected_doctor_id,
    }
    return render(request, 'appointments/admin_edit_booking.html', context)

@user_passes_test(is_admin)
def admin_cancel_booking_view(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    if request.method == 'POST':
        booking.slot.is_booked = False
        booking.slot.save()
        booking.delete()
    return redirect('admin_booking_list')

@user_passes_test(is_admin)
def admin_doctor_list_view(request):
    doctors = Doctor.objects.all()
    return render(request, 'appointments/admin_doctor_list.html', {'doctors': doctors})

# Add Doctor
@user_passes_test(is_admin)
def admin_add_doctor_view(request):
    if request.method == 'POST':
        form = DoctorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_doctor_list')
    else:
        form = DoctorForm()
    return render(request, 'appointments/admin_add_doctor_form.html', {'form': form})

@user_passes_test(is_admin)
def admin_edit_doctor_view(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id)
    if request.method == 'POST':
        form = DoctorForm(request.POST, instance=doctor)
        if form.is_valid():
            form.save()
            return redirect('admin_doctor_list')
    else:
        form = DoctorForm(instance=doctor)
    return render(request, 'appointments/admin_add_doctor_form.html', {'form': form, 'title': 'Edit Doctor'})

@user_passes_test(is_admin)
def admin_delete_doctor_view(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id)
    if request.method == 'POST':
        doctor.delete()
    return redirect('admin_doctor_list')


@user_passes_test(is_admin)
def admin_slot_list_view(request):
    slots = AppointmentSlot.objects.all()
    now_local = timezone.localtime()
    return render(request, 'appointments/admin_slot_list.html', {
        'slots': slots,
        'today_date': now_local.date(),
        'current_time': now_local.time(),
        'search_query': request.GET.get('q', '')
    })

@user_passes_test(is_admin)
def admin_add_slot_view(request):
    if request.method == 'POST':
        form = SlotForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_slot_list')
    else:
        form = SlotForm()
    return render(request, 'appointments/admin_add_slot_form.html', {
        'form': form,
        'today_date': timezone_today().isoformat(),
        'title': 'Add Appointment Slot'})

@user_passes_test(is_admin)
def admin_edit_slot_view(request, slot_id):
    slot = get_object_or_404(AppointmentSlot, id=slot_id)
    if request.method == 'POST':
        form = SlotForm(request.POST, instance=slot)
        if form.is_valid():
            form.save()
            return redirect('admin_slot_list')
    else:
        form = SlotForm(instance=slot)
    return render(request, 'appointments/admin_add_slot_form.html', {'form': form, 'title': 'Edit Appointment Slot'})
@user_passes_test(is_admin)
def admin_delete_slot_view(request, slot_id):
    slot = get_object_or_404(AppointmentSlot, id=slot_id)
    if request.method == 'POST':
        slot.delete()
    return redirect('admin_slot_list')

@user_passes_test(is_admin)
def admin_user_list_view(request):
    search_query = request.GET.get('q', '')
    if search_query:
        users_list = User.objects.filter(username__icontains=search_query) | User.objects.filter(
            email__icontains=search_query)
    else:
        users_list = User.objects.all().order_by('-date_joined')

    paginator = Paginator(users_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'appointments/admin_user_list.html', {
        'page_obj': page_obj,
        'search_query': search_query
    })

@user_passes_test(is_admin)
def admin_create_user_view(request):
    if request.method == 'POST':
        form = CustomUserCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"User {user.username} create successfully！")
            return redirect('admin_user_list')
    else:
        form = CustomUserCreateForm()

    return render(request, 'appointments/admin_add_user_form.html', {'form': form})

@user_passes_test(is_admin)
def admin_edit_user_view(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        form = EditUserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('admin_user_list')
    else:
        form = EditUserForm(instance=user)
    return render(request, 'appointments/admin_edit_user_form.html', {'form': form, 'title': 'Edit User'})

@user_passes_test(is_admin)
def admin_suspend_user_view(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_active = False
    user.save()
    return redirect('admin_user_list')

@user_passes_test(is_admin)
def admin_active_user_view(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_active = True
    user.save()
    return redirect('admin_user_list')

@user_passes_test(is_admin)
def admin_delete_user_view(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        user.delete()
    return redirect('admin_user_list')

@login_required
def patient_book_list_view(request):
    bookings = Booking.objects.filter(patient=request.user).select_related('slot__doctor')
    now_local = timezone.localtime()
    return render(request, 'appointments/patient_book_list.html', {
        'bookings': bookings,
        'today_date': now_local.date(),
        'current_time': now_local.time(),
        'search_query': request.GET.get('q', '')
    })

@login_required
def patient_add_booking_view(request):
    doctors = Doctor.objects.all()
    selected_doctor_id = request.GET.get('doctor_id')

    if not selected_doctor_id and doctors.exists():
        selected_doctor_id = str(doctors.first().id)

    if request.method == 'POST':
        # Pass doctor_id when binding POST request
        form = PatientEditBookingForm(request.POST, doctor_id=selected_doctor_id)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.patient = request.user
            booking.save()

            slot = booking.slot
            slot.is_booked = True
            slot.save()

            messages.success(request, "Booking added successfully!")
            return redirect('patient_book_list')
    else:
        # Pass doctor_id on GET request
        form = PatientEditBookingForm(doctor_id=selected_doctor_id)

    return render(request, 'appointments/patient_add_booking.html', {
        'form': form,
        'doctors': doctors,
        'selected_doctor_id': selected_doctor_id,
        'title': 'Add New Booking'
    })

@login_required
def patent_edit_booking_view(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, patient=request.user)
    selected_doctor_id = request.GET.get('doctor_id', str(booking.slot.doctor.id))
    if request.method == 'POST':
        old_slot = booking.slot
        form = PatientEditBookingForm(request.POST, instance=booking, doctor_id=selected_doctor_id)

        if form.is_valid():
            new_booking = form.save(commit=False)

            if old_slot != new_booking.slot:
                old_slot.is_booked = False
                old_slot.save()
                new_booking.slot.is_booked = True
                new_booking.slot.save()

            new_booking.save()
            messages.success(request, "Booking updated successfully!")
            return redirect('patient_book_list')
    else:
        form = PatientEditBookingForm(instance=booking, doctor_id=selected_doctor_id)

    doctors = Doctor.objects.all()
    return render(request, 'appointments/patient_edit_booking.html',
                  {'form': form,
                   'booking': booking,
                   'doctors': doctors,
                   'selected_doctor_id': selected_doctor_id,
                   'title': 'Edit Booking'
                   })

@login_required
def patient_cancel_booking_view(request,booking_id):
    booking = get_object_or_404(Booking, id=booking_id, patient=request.user)
    if request.method == 'POST':
        booking.slot.is_booked=False
        booking.slot.save()
        booking.delete()
        messages.success(request, "Booking cancelled successfully!")
        return redirect('patient_book_list')
    return redirect('patient_book_list')














