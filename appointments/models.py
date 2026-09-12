from django.db import models
from django.contrib.auth.models import User

# Doctor Profile
class Doctor(models.Model):
    name = models.CharField(max_length=100)
    specialization = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)

    def __str__(self):
        return f"Dr. {self.name} ({self.specialization})"

# Appointment Slot
class AppointmentSlot(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='slots')
    date = models.DateField()
    time = models.TimeField()
    is_booked = models.BooleanField(default=False)

    class Meta:
        # Prevents duplicate slots for the same doctor at the same time
        unique_together = ('doctor', 'date', 'time')

    def __str__(self):
        return f"{self.doctor.name} - {self.date} at {self.time}"

# Patient Booking
class Booking(models.Model):
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    slot = models.OneToOneField(AppointmentSlot, on_delete=models.CASCADE) # Prevents double booking
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient.username} - {self.slot}"