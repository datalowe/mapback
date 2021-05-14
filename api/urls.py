from django.urls import path

from rest_framework.authtoken import views as drf_views

from . import views

app_name = 'api'
urlpatterns = [
    path('token-auth/', drf_views.obtain_auth_token, name='obtain-auth-token'),
    path('register/', views.CreateUser.as_view(), name='create-user'),
    path('locations/', views.LocationsListCreate.as_view(), name='locations-lc'),
    path('locations/<int:pk>/', views.LocationsRetrieveUpdateDestroy.as_view(), name='locations-rud'),
]
