from django.contrib.auth import get_user_model

from rest_framework import authentication, permissions
from rest_framework.generics import RetrieveUpdateAPIView, ListCreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView



from .serializers import LocationSerializer
from locations.models import Location

class LocationsListCreate(ListCreateAPIView):
    """
    View to list all of the user's locations.

    * Requires token authentication.
    """
    queryset= Location.objects.all()
    serializer_class = LocationSerializer
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def filter_queryset(self, queryset):
        return queryset.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

class LocationsRetrieveUpdateDestroy(RetrieveUpdateAPIView):
    """
    View to retrieve a single location, or update it,
    or destroy it.

    * Requires token authentication.
    """
    queryset= Location.objects.all()
    serializer_class = LocationSerializer
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def filter_queryset(self, queryset):
        return queryset.filter(owner=self.request.user)


class CreateUser(APIView):
    """
    View to register/create a new user.
    """
    def post(self, request, format=None):
        """
        Create a new user.
        """
        check_keys = ('username', 'password')
        if any([key not in request.data for key in check_keys]):
            return Response(
                {'message': 'Both username and password must be included'},
                status=400
            )
        if len(request.data['password']) < 6:
            return Response(
                {'message': 'Password must be at least 6 characters long.'},
                status=400
            )
        if len(request.data['username']) < 3:
            return Response(
                {'message': 'Username must be at least 3 characters long.'},
                status=400
            )
        if get_user_model().objects.filter(username=request.data['username']).exists():
            return Response(
                {'message': 'That username is not available.'},
                status=409
            )
        get_user_model().objects.create_user(
            username=request.data['username'], 
            password=request.data['password']
        )
        return Response({'message': 'User created!'}, status=201)
