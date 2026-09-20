from datetime import datetime
from importlib.metadata import requires

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models import Q

from django.utils import timezone

from appointments.models import Doctor, AppointmentSlot, Booking


class DoctorForm(forms.ModelForm):
    class Meta:
        model = Doctor
        fields = ['name', 'specialization', 'email', 'phone']

class SlotForm(forms.ModelForm):
    class Meta:
        model = AppointmentSlot
        fields = ['doctor', 'date', 'time']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'doctor': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        slot_date = cleaned_data.get('date')
        slot_time = cleaned_data.get('time')
        if slot_date and slot_time:
            slot_datetime = datetime.combine(slot_date, slot_time)
            slot_datetime = timezone.make_aware(slot_datetime)

            if slot_datetime < timezone.now():
                raise ValidationError("Cannot create or update a slot in the past.")
        return cleaned_data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['date'].widget.attrs['min'] = timezone.now().date().isoformat()
        # If edit the slot, the slot is existed in the database
        if self.instance and self.instance.pk:
            self.fields['doctor'].disabled = True

class CustomUserCreateForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Email Address")
    first_name = forms.CharField(max_length=30, required=False, label="First Name")
    last_name = forms.CharField(max_length=30, required=False, label="Last Name")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ['username', 'first_name', 'last_name', 'email',]

class EditUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CustomSlotChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f"{obj.date} at {obj.time.strftime('%H:%M')}"


class PatientEditBookingForm(forms.ModelForm):
    slot = CustomSlotChoiceField(
        queryset=AppointmentSlot.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="- Select a time slot -"
    )

    class Meta:
        model = Booking
        fields = ['slot']

    def __init__(self, *args, doctor_id=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Get local time
        now_local = timezone.localtime()
        today_date = now_local.date()
        current_time = now_local.time()

        # filter the passed slots
        # 1. date > today OR
        # 2. date = today and time >= current time
        future_slots = Q(date__gt=today_date) | Q(date=today_date, time__gte=current_time)

        queryset = AppointmentSlot.objects.filter(is_booked=False).filter(future_slots)

        # If editing an existing booking, include its current slot even if it's already marked is_booked=True
        if self.instance and self.instance.pk and hasattr(self.instance, 'slot') and self.instance.slot:
            queryset = AppointmentSlot.objects.filter(
                (Q(is_booked=False) & future_slots) | Q(id=self.instance.slot.id)
            )

        # Filter by doctor
        if doctor_id:
            queryset = queryset.filter(doctor_id=doctor_id)

        self.fields['slot'].queryset = queryset.order_by('date', 'time')