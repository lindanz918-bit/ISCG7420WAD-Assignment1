from django import forms

from appointments.models import Doctor, AppointmentSlot


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