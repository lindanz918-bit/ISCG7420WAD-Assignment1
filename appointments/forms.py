from datetime import datetime
from importlib.metadata import requires

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from django.db.models import Q

from django.utils import timezone

from appointments.models import Doctor, AppointmentSlot, Booking


class DoctorForm(forms.ModelForm):
    class Meta:
        model = Doctor
        fields = ['username', 'first_name', 'last_name', 'specialization', 'email', 'phone', 'experience']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'specialization': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'experience': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter doctor\'s qualifications, years of experience, expertise, background, etc.'
            }),
        }


class DoctorChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        first_name = obj.first_name if obj.first_name else ''
        last_name = obj.last_name if obj.last_name else ''
        full_name = f"{first_name} {last_name}".strip()

        if full_name:
            return f"Dr. {full_name} (@{obj.username})"
        return f"Dr. {obj.username} (@{obj.username})"

class SlotForm(forms.ModelForm):
    doctor = DoctorChoiceField(
        queryset=Doctor.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="- Select a Doctor -"
    )

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


class CustomUserCreateForm(forms.ModelForm):
    email = forms.EmailField(required=True, label="Email Address")
    first_name = forms.CharField(max_length=30, required=False, label="First Name")
    last_name = forms.CharField(max_length=30, required=False, label="Last Name")

    group = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        required=False,
        label="User Role / Group",
        empty_label="- Select Group -",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

    def save(self, commit=True):
        user = super().save(commit=False)

        user.set_password('123456')

        if commit:
            user.save()

            selected_group = self.cleaned_data.get('group')
            if selected_group:
                user.groups.add(selected_group)
            else:
                patient_group, _ = Group.objects.get_or_create(name='Patient')
                user.groups.add(patient_group)

            if selected_group and selected_group.name == 'Doctor':
                doc_email = user.email
                if Doctor.objects.filter(email=doc_email).exclude(username=user.username).exists():
                    doc_email = f"{user.username}_{user.email}"

                Doctor.objects.get_or_create(
                    user=user,
                    defaults={
                        'username': user.username,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'email': doc_email,
                        'specialization': 'General',
                        'phone': 'N/A'
                    }
                )
        return user

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            if field_name == 'group':
                field.widget.attrs.update({'class': 'form-select'})
            else:
                field.widget.attrs.update({'class': 'form-control'})


class EditUserForm(forms.ModelForm):
    group = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        required=False,
        label="User Role / Group",
        empty_label="- Select Group -",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_active', 'group']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.groups.exists():
            self.fields['group'].initial = self.instance.groups.first().id

    def save(self, commit=True):
        user = super().save(commit=commit)
        selected_group = self.cleaned_data.get('group')

        user.groups.clear()

        if selected_group:
            user.groups.add(selected_group)

            if selected_group.name == 'Doctor':
                doc_email = user.email
                if Doctor.objects.filter(email=doc_email).exclude(username=user.username).exists():
                    doc_email = f"{user.username}_{user.email}"

                doctor, created = Doctor.objects.get_or_create(
                    username=user.username,
                    defaults={
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'email': doc_email,
                        'specialization': 'General',
                        'phone': 'N/A'
                    }
                )
                if not created:
                    doctor.first_name = user.first_name
                    doctor.last_name = user.last_name
                    doctor.email = doc_email
                    doctor.save()

        return user

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