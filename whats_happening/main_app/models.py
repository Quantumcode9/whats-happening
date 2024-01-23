from django.db import models
from django.contrib.auth.models import User
from datetime import date


# Create your models here.
    
class Venue(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    description = models.TextField(max_length=250)
    # image = models.ImageField(upload_to='images/', blank=True)
    
    def __str__(self):
        return self.name


class Reservation(models.Model):
    attendee = models.ForeignKey(User, on_delete=models.CASCADE)
    guests = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.attendee} - guests: {self.guests}"
    

class Event(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(max_length=250)
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, null=True, blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    end_time = models.TimeField(null=True, blank=True)

    # recurring = models.BooleanField(default=False)
    reservations = models.ManyToManyField(Reservation)
    # recurrences = models.ForeignKey('Recurrences', on_delete=models.CASCADE, null=True, blank=True)
    # image = models.ImageField(upload_to='images/', blank=True)

    # externalID
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['date']
    
    

