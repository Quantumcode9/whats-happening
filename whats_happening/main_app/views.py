import datetime

from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import ListView
from django.views.generic.detail import DetailView
from django.db.models import Q

from .models import Event

from django.views.generic import ListView

from .models import Event, Venue

# Create your views here.
def home(request):
    return render(request, 'home.html')
  
  
def about(request):
    return render(request, 'about.html')

def event_search(request):
    return render(request, 'events/search.html')
  
def event_detail(request, event_id):
    event = Event.objects.get(id=event_id)
    return render(request, 'events/detail.html', {'event': event})


## Event Views
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


class SearchResultsList(EventList):
  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context['page_title'] = 'Search Results'
    return context
  
  def get_queryset(self):
    q_objects = Q()

    # Search by event_name
    event_name = self.request.GET.get("event_name")
    if event_name:
      print('adding event_name to query')
      q_objects &= Q(name__icontains=event_name)
    
    # Search by venue
    venue = self.request.GET.get("venue")
    if venue:
      q_objects &= Q(venue__name__icontains=venue)

    # Always filter out past events
    return Event.objects.filter(q_objects, date__gte=datetime.date.today())

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
  fields = ['name', 'venue', 'description', 'date', 'time',]
  success_url = '/events'
  

class EventEdit(UpdateView):
    model = Event
    fields = ['name', 'date', 'time', 'end_time', 'venue']
    success_url = '/events'

class EventDelete(DeleteView):
    model = Event
    success_url = '/events'
  
  
  