from django.contrib import admin

from .models import Event, Venue, Reservation

# Register your models here.
admin.site.register(Event)
admin.site.register(Venue)
admin.site.register(Reservation)
