from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    # path('about/', views.about, name='about')
    path('events/', views.EventList.as_view(), name='index'),
    path('events/myowned/', views.MyOwnedEventList.as_view(), name='myownedindex'),
    path('events/myowned/include_past', views.MyOwnedWithPastEventList.as_view(), name='myownedindex_withpast'),
    # path('events/mine', views.MyEventList.as_view(), name='myindex'),

    path('accounts/signup/', views.signup, name='signup'),
]