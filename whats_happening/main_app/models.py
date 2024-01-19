from django.db import models
from django.contrib.auth.models import User

# Create your models here.
#
    
class Venue(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    description = models.TextField(max_length=250)
    # image = models.ImageField(upload_to='images/', blank=True)
    
    def __str__(self):
        return self.name
    

class Event(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(max_length=250)
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, null=True, blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    end_time = models.TimeField(null=True, blank=True)

    # recurring = models.BooleanField(default=False)
    # reservations = models.ManyToManyField('Reservation', blank=True)
    # recurrences = models.ForeignKey('Recurrences', on_delete=models.CASCADE, null=True, blank=True)
    # image = models.ImageField(upload_to='images/', blank=True)
    
    def __str__(self):
        return self.name
    
    

# class Reservation(models.Model):
#     name = models.CharField(max_length=100)
#     guests = models.IntegerField()
    
    
#     def __str__(self):
#         return self.name
