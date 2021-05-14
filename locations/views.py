from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from django.urls import reverse_lazy

from .models import Location


# class LocationCreateView(LoginRequiredMixin, CreateView):
#     model = Location
#     template_name = 'locations/location-create.html'
#     fields = [
#         'place_name', 'address', 'latitude', 
#         'longitude', 'business_hours',
#         'description', 'priority', 'icon'
#     ]
#     success_url = reverse_lazy('locations:location-list')


# class LocationDeleteView(LoginRequiredMixin, DeleteView):
#     model = Location
#     template_name = 'locations/location-delete.html'
#     success_url = reverse_lazy('locations:location-list')


# class LocationDetailView(LoginRequiredMixin, DetailView):
#     model = Location
#     context_object_name = 'location'
#     template_name = 'locations/location-detail.html'


# class LocationListView(LoginRequiredMixin, ListView):
class LocationListView(ListView):
    model = Location
    context_object_name = 'locations'
    template_name = 'locations/location-list.html'


# class LocationUpdateView(LoginRequiredMixin, UpdateView):
#     model = Location
#     template_name = 'locations/location-update.html'
#     fields = ['place_name', 'latitude', 'longitude', 'business_hours',
#               'description', 'priority', 'icon']


# def login_view(request):
#     if request.method == "POST":
#         username = request.POST.get('username')
#         password = request.POST.get('password')
#         user = authenticate(request, username=username, password=password)
#         if user is not None:
#             login(request, user)
#             return redirect('locations:location-list')
#         else:
#             return redirect('login-form')
#     else:
#         return redirect('login-form')


# def logout_view(request):
#     logout(request)
#     return redirect('locations:location-list')
