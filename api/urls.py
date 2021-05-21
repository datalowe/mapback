from django.urls import path

from rest_framework.authtoken import views as drf_views

from . import views

app_name = 'api'
urlpatterns = [
    path(
        'token-auth/', 
        drf_views.obtain_auth_token, 
        name='obtain-auth-token'
    ),
    path(
        'register/', 
        views.CreateUser.as_view(), 
        name='create-user'
    ),
    path(
        'locations/', 
        views.LocationsListCreate.as_view(), 
        name='locations-lc'
    ),
    path(
        'locations/<int:pk>/', 
        views.LocationsRetrieveUpdateDestroy.as_view(), 
        name='locations-rud'
    ),
    path(
        'markersignificances/', 
        views.MarkerSignificancesListOrCreate.as_view(), 
        name='markersignificances-lc'
    ),
    path(
        'markersignificances/<int:pk>/', 
        views.MarkerSignificancesRetrieveUpdateDestroy.as_view(), 
        name='markersignificances-rud'
    ),
    path(
        'markericons/', 
        views.MarkerIconsList.as_view(), 
        name='markericons-l'
    ),
    path(
        'forecasts/',
        views.ForecastPointList.as_view(),
        name='forecasts-l'
    )
]
