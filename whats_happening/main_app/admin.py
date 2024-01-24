from django.contrib import admin

from .models import Event, Venue, Reservation, Photo, Profile


# Register your models here.
admin.site.register(Event)
admin.site.register(Venue)
admin.site.register(Reservation)
admin.site.register(Photo)
admin.site.register(Profile)