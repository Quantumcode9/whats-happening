import datetime
import uuid
import boto3
import os

from botocore.exceptions import NoCredentialsError
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

from django.contrib.auth.forms import UserCreationForm
from django.db.models import Q
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import ListView
from django.views.generic.detail import DetailView
from django.utils.dateparse import parse_date, parse_time
from django.contrib.auth.models import User

from .models import Event, Venue, Reservation, Profile
from .forms import EventForm, VenueForm, SearchForm, ProfileForm 
from .forms import PhotoForm 
from .models import Photo

from .ticketmaster_api import get_ticketmaster_events
from .ticketmaster_api import get_event_details

# Create your views here.
def home(request):
    return render(request, 'home.html')

def about(request):
    return render(request, 'about.html')

def event_search(request):
    return render(request, 'events/search.html')


def events_index(request):
    events = Event.objects.all()
    return render(request, 'events/index.html', {'events': events})

# API call event search by keyword
def parse_api_event_data(events_data):
    events = []
    if events_data:
        for event in events_data.get('_embedded', {}).get('events', []):
            embedded = event.get('_embedded', {})
            venues = embedded.get('venues') if embedded else []
            venue_name = venues[0].get('name') if venues else None
            date_str = event.get('dates', {}).get('start', {}).get('localDate')
            time_str = event.get('dates', {}).get('start', {}).get('localTime')
            event_info = {
                'id': event.get('id'),
                'name': event.get('name'),
                'description': event.get('description'),
                'date': parse_date(date_str) if date_str else None,
                'time': parse_time(time_str) if time_str else None,
                'image_url': event.get('images', [])[0].get('url') if event.get('images') else None,
                'venue': venue_name
            }
            events.append(event_info)

    return events

def get_api_results_for_keyword(keyword):
    events_data = get_ticketmaster_events(keyword)
    return parse_api_event_data(events_data)

def get_api_results_for_keyword_and_date(keyword, date):
    events_data = get_ticketmaster_events(keyword, date)
    return parse_api_event_data(events_data)

# Api call event by id
def event_detail(request, event_id):
    event_data = get_event_details(event_id)  
#####
    # print(event_data)
#####
    if event_data:
        event_info = {
            'name': event_data.get('name'),
            'description': event_data.get('description'),
            'images': event_data.get('images', []),
            'venue': event_data.get('_embedded', {}).get('venues', [])[0].get('name') if event_data.get('_embedded', {}).get('venues') else None,
            'externalLinks': {
                'youtube': event_data.get('externalLinks', {}).get('youtube', [{}])[0].get('url') if event_data.get('externalLinks', {}).get('youtube') else None,
                'twitter': event_data.get('externalLinks', {}).get('twitter', [{}])[0].get('url') if event_data.get('externalLinks', {}).get('twitter') else None,
            },
            'info': event_data.get('info'),
            'location': {
                'address': event_data.get('_embedded', {}).get('venues', [])[0].get('address', {}).get('line1') if event_data.get('_embedded', {}).get('venues') else None,
                'city': event_data.get('_embedded', {}).get('venues', [])[0].get('city', {}).get('name') if event_data.get('_embedded', {}).get('venues') else None,
                'state': event_data.get('_embedded', {}).get('venues', [])[0].get('state', {}).get('name') if event_data.get('_embedded', {}).get('venues') else None,
                'country': event_data.get('_embedded', {}).get('venues', [])[0].get('country', {}).get('name') if event_data.get('_embedded', {}).get('venues') else None,
            },
            'start_date': event_data.get('dates', {}).get('start', {}).get('localDate'),
            'start_time': event_data.get('dates', {}).get('start', {}).get('localTime'),
        }
        print(event_info)
        return render(request, 'events/categories/event_detail.html', {'event': event_info})
    else:
        return HttpResponse("Event not found or an error occurred.")



## Event Index List Views
class EventList(ListView):
    model = Event
    template_name = 'events/index.html'
    
    def get_queryset(self):
        return Event.objects.filter(date__gte=datetime.date.today())

class MyEventList(EventList):
    def get_queryset(self):
        return Event.objects.filter(
            (Q(owner=self.request.user) | Q(reservations__attendee=self.request.user)) &
            Q(date__gte=datetime.date.today())
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'My Events'
        context['show_filter_options'] = True
        context['past_filter'] = 'hide'
        context['event_filter'] = 'all'
        return context
    
class MyWithPastEventList(MyEventList):
    def get_queryset(self):
        return Event.objects.filter(
            (Q(owner=self.request.user) | Q(reservations__attendee=self.request.user))
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['past_filter'] = 'show'
        return context
    
class MyOwnedEventList(MyEventList):
    def get_queryset(self):
        return Event.objects.filter(owner=self.request.user, date__gte=datetime.date.today())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'My Owned Events'
        context['show_filter_options'] = True
        context['past_filter'] = 'hide'
        context['event_filter'] = 'owned'
        return context

class MyOwnedWithPastEventList(MyOwnedEventList):
    def get_queryset(self):
        return Event.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['past_filter'] = 'show'
        return context

class SearchResultsList(EventList):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Search Results'

        # Get external api search results and send onto template
        keyword = self.request.GET.get('keyword')
        date = self.request.GET.get('date')
        if date:
            context['external_event_list'] = get_api_results_for_keyword_and_date(keyword, date)
        else: 
            context['external_event_list'] = get_api_results_for_keyword(keyword)
        return context

    def get_queryset(self):
        q_objects = Q()

        # Keyword search checks event_name, venue_name, venue_description
        keyword = self.request.GET.get('keyword')
        if keyword:
            q_objects |= Q(name__icontains=keyword)
            q_objects |= Q(venue__name__icontains=keyword)
            q_objects |= Q(venue__location__icontains=keyword)

        # Search by date
        date = self.request.GET.get('date')
        if date:
            q_objects &= Q(date__gte=date)
        else:
            # If no date picked, filter out past events
            q_objects &= Q(date__gte=datetime.date.today())

        return Event.objects.filter(q_objects)


class DetailView(DetailView):
  model = Event
  template_name = 'events/detail.html'


def event_detail_model(request, event_id):
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
def assoc_external_reservation(request):
    # Create the reservation
    reservation = Reservation()
    reservation.attendee = request.user
    reservation.guests = request.POST["guests"]
    reservation.save()

    # Add it to the event
    # create an event from ticketmaster!


    # 'image_url': event.get('images', [])[0].get('url') if event.get('images') else None,
    # 'venue': venue_name

    event = Event()
    event.name = request.POST["name"]
    event.description = request.POST["description"]
    event.date = parse_date(request.POST["date"])
    event.time = parse_time(request.POST["time"])
    event.owner = User.objects.get(username='TheMachine')
    event.save()

    event.reservations.add(reservation)

    # Redirect to event detail
    return redirect('detail', event_id=event.id)

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

    return redirect('detail', event_id=event_id)


def event_hub(request):
    my_owned_events = Event.objects.filter(owner=request.user, date__gte=datetime.date.today())
    my_rsvp_events = Event.objects.filter(reservations__attendee=request.user, date__gte=datetime.date.today())
    keyword = request.user.profile.keyword if request.user.profile.keyword else "music"
    pref_events = get_api_results_for_keyword(keyword)
    return render(request, 'events/hub.html', { 
        'my_owned_events': my_owned_events, 
        'my_rsvp_events': my_rsvp_events, 
        'pref_events': pref_events
    })

class ProfileCreate(LoginRequiredMixin, CreateView):
    model = Profile
    fields = [ 'keyword' ]

    def form_valid(self, form):
        profile = form.save(commit=False)
        profile.user = self.request.user
        return super(ProfileCreate, self).form_valid(form)
        # return http.HttpResponseRedirect(self.get_success_url())

class ProfileUpdate(LoginRequiredMixin, UpdateView):
    model = Profile
    fields = [ 'keyword' ]
