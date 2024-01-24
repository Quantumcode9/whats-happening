from django.db import models
from django.contrib.auth.models import User
from datetime import date
from django.utils import timezone
from django.urls import reverse

from django.db.models.signals import post_save
from django.dispatch import receiver


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

    # api_event_id - character
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['date']
    
# class Photo(models.Model):
#   image = models.ImageField(upload_to='photos/')
#   description = models.TextField()

# Associate with specific venues
    
class Photo(models.Model):
    image_url = models.URLField()
    description = models.TextField()
    event = models.ForeignKey(Event, on_delete=models.CASCADE)

    def __str__(self):
        return f"Photo for event: {self.event.name} @{self.image_url}"
    

# User Profile Model
# This will store a default keyword, city or zip code to search by
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    keyword = models.CharField(max_length=100)
    
    def __str__(self):
        return f"Profile for { self.user }"
    
    # this is the get_absolute_url method
    # it redirects to the detail page where appropriate
    def get_absolute_url(self):
        return reverse('hub', kwargs={})
# @receiver(post_save, sender=User)
# def create_user_profile(sender, instance, created, **kwargs):
#     if created:
#         Profile.objects.create(user=instance)

# @receiver(post_save, sender=User)
# def save_user_profile(sender, instance, **kwargs):
#     instance.profile.save()
