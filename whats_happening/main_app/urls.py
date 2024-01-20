from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),

#    path('events/', views.events_index, name='index'),
#    path('events/<int:event_id>/', views.events_detail, name='detail'),
    path('events/', views.EventList.as_view(), name='index'),
    path('events/myowned/', views.MyOwnedEventList.as_view(), name='myownedindex'),
    path('events/myowned/include_past', views.MyOwnedWithPastEventList.as_view(), name='myownedindex_withpast'),
    path('events/search', views.event_search, name='search'),
    path('events/searchresults', views.SearchResultsList.as_view(), name='search_results'),
    # path('events/mine', views.MyEventList.as_view(), name='myindex'), 
    path('events/create/', views.EventCreate.as_view(), name='events_create'),

    path('accounts/signup/', views.signup, name='signup'),
]