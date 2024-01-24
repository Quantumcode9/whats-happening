import datetime
import uuid
import boto3
import os

from botocore.exceptions import NoCredentialsError
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Q
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import ListView
from django.views.generic.detail import DetailView
from .models import Event, Venue, Reservation
from .forms import EventForm
from .forms import VenueForm 
from .forms import PhotoForm 
from .models import Photo


# Create your views here.
def home(request):
    return render(request, 'home.html')
  
def about(request):
    return render(request, 'about.html')

def event_search(request):
    return render(request, 'events/search.html')

## Event Index List Views
class EventList(ListView):
    model = Event
    template_name = 'events/index.html'
    
    def get_queryset(self):
        return Event.objects.filter(date__gte=datetime.date.today())
  
class MyOwnedEventList(EventList):
    def get_queryset(self):
        return Event.objects.filter(owner=self.request.user, date__gte=datetime.date.today())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'My Owned Events'
        context['showhide_past_option'] = True
        context['include_past'] = False
        return context
  
class MyOwnedWithPastEventList(MyOwnedEventList):
    def get_queryset(self):
        return Event.objects.filter(owner=self.request.user)
  
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['showhide_past_option'] = True
        context['include_past'] = True
        return context

class DetailView(DetailView):
  model = Event
  template_name = 'events/detail.html'


def event_detail(request, event_id):
    event = Event.objects.get(id=event_id)
    try:
      reservation = event.reservations.get(attendee=request.user)
      print(event)
      return render(request, 'events/detail.html', {'event': event, 'reservation': reservation})
    except Reservation.DoesNotExist: 
      return render(request, 'events/detail.html', {'event': event})

@login_required
def assoc_reservation(request, event_id):
    # Create the reservation
    reservation = Reservation()
    reservation.attendee = request.user
    reservation.guests = request.POST["guests"]
    reservation.save()

    # Add it to the event
    Event.objects.get(id=event_id).reservations.add(reservation)

    # Redirect to event detail
    return redirect('detail', event_id=event_id)

@login_required
def unassoc_reservation(request, event_id, reservation_id):
    # Target the event
    Event.objects.get(id=event_id).reservations.remove(reservation_id)
    # Redirect to event detail
    return redirect('detail', event_id=event_id)

@login_required
def edit_reservation(request, event_id, reservation_id):
    # Target the event, update guests, and save
    reservation = Event.objects.get(id=event_id).reservations.get(id=reservation_id) 
    reservation.guests = request.POST["guests"]
    reservation.save()

    # Redirect to event detail
    return redirect('detail', event_id=event_id)

class SearchResultsList(EventList):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Search Results'
        return context
  
    def get_queryset(self):
        q_objects = Q()

        # Search by event_name
        event_name = self.request.GET.get('event_name')
        if event_name:
            q_objects &= Q(name__icontains=event_name)
        
        # Search by venue
        venue = self.request.GET.get('venue')
        if venue:
            q_objects &= Q(venue__name__icontains=venue)

        # Search by date
        date = self.request.GET.get('date')
        if date:
            q_objects &= Q(date=date)
        else:
            # If no date picked, filter out past events
            q_objects &= Q(date__gte=datetime.date.today())

        return Event.objects.filter(q_objects)

def signup(request):
  error_message = ''
  if request.method == 'POST':
    # This is how to create a 'user' form object
    # that includes the data from the browser
    form = UserCreationForm(request.POST)
    if form.is_valid():
      # This will add the user to the database
      user = form.save()
      # This is how we log a user in via code
      login(request, user)
      return redirect('home')
    else:
      error_message = 'Invalid sign up - try again'
  # A bad POST or a GET request, so render signup.html with an empty form
  form = UserCreationForm()
  context = {'form': form, 'error_message': error_message}
  return render(request, 'registration/signup.html', context)

class EventCreate(CreateView):
  model = Event
  form_class = EventForm
  success_url = '/events'
  
  def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)
  

class EventEdit(UpdateView):
    model = Event
    fields = ['name', 'date', 'time', 'end_time', 'venue']
    success_url = '/events'

class EventDelete(DeleteView):
    model = Event
    success_url = '/events'
  
  
  # Views for Venue
def venue_list(request):
    venues = Venue.objects.all()
    return render(request, 'venues/list.html', {'venues': venues})

def venue_detail(request, pk):
    venue = get_object_or_404(Venue, pk=pk)
    return render(request, 'venues/detail.html', {'venue': venue})

def venue_create(request):
    if request.method == 'POST':
        form = VenueForm(request.POST)
        if form.is_valid():
            venue = form.save(commit=False)
            venue.save()
            return redirect('venue_list')
    else:
        form = VenueForm()
    return render(request, 'venues/form.html', {'form': form})

def venue_update(request, pk):
    venue = get_object_or_404(Venue, pk=pk)
    if request.method == 'POST':
        form = VenueForm(request.POST, instance=venue)
        if form.is_valid():
            venue = form.save(commit=False)
            venue.save()
            return redirect('venue_list')
    else:
        form = VenueForm(instance=venue)
    return render(request, 'venues/form.html', {'form': form})

def venue_delete(request, pk):
    venue = get_object_or_404(Venue, pk=pk)
    venue.delete()
    return redirect('venue_list')

def add_event_photo(request, event_id):
    event = Event.objects.get(pk=event_id)
    photo_file = request.FILES.get('photo-file', None)

    if not os.environ.get('S3_BUCKET'):
        print('S3_BUCKET environment variable is not defined.')
        return redirect('event_detail', event_id=event_id)

    if photo_file:
        try:
            s3 = boto3.client('s3')
            key = uuid.uuid4().hex[:6] + photo_file.name[photo_file.name.rfind('.'):]
            bucket = os.environ['S3_BUCKET']
            s3.upload_fileobj(photo_file, bucket, key)
            url = f"{os.environ['S3_BASE_URL']}{bucket}/{key}"
            Photo.objects.create(image_url=url, description="Your description here", event_id=event_id)
        except Exception as e:
            print('An error occurred uploading file to S3')
            print(e)

    return redirect('event_detail', event_id=event_id)
       