from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    # path('about/', views.about, name='about')
    path('events/', views.EventList.as_view(), name='index'),

    path('accounts/signup/', views.signup, name='signup'),
]