import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Q
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import ListView
from django.views.generic.detail import DetailView
from django.utils.dateparse import parse_date, parse_time

from .models import Event, Venue, Reservation
from .forms import EventForm, VenueForm, SearchForm 

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

# Api call event by id
def event_detail(request, event_id):
    api_key = 'TwGGLlIhPr3PtugWAMYtjGdnJwGdQTYs' 
    event_data = get_event_details(api_key, event_id)  
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
        context['external_event_list'] = self.get_api_results_for_keyword(keyword, date)

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

    def get_api_results_for_keyword(request, keyword, date):
        api_key = 'TwGGLlIhPr3PtugWAMYtjGdnJwGdQTYs'  # Add this to your ENV variables
        # keyword = 'music'  # default keyword

        events_data = get_ticketmaster_events(api_key, keyword, date)
        # print(events_data)
        events = []

        if events_data:
            for event in events_data.get('_embedded', {}).get('events', []):
                embedded = event.get('_embedded', {})
                venues = embedded.get('venues') if embedded else []
                venue_name = venues[0].get('name') if venues else None
                event_info = {
                    'id': event.get('id'),
                    'name': event.get('name'),
                    'description': event.get('description'),
                    'date': parse_date(event.get('dates', {}).get('start', {}).get('localDate')),
                    'time': parse_time(event.get('dates', {}).get('start', {}).get('localTime')),
                    'image_url': event.get('images', [])[0].get('url') if event.get('images') else None,
                    'venue': venue_name
                }
                events.append(event_info)

        return events


class DetailView(DetailView):
  model = Event
  template_name = 'events/detail.html'


def event_detail_model(request, event_id):
    event = Event.objects.get(id=event_id)
    try:
      reservation = event.reservations.get(attendee=request.user)
      print(reservation)
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