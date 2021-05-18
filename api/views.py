from django.contrib.auth import get_user_model
from django.db.models import Q

from rest_framework import authentication
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ValidationError
from rest_framework.generics import (
    ListAPIView, 
    RetrieveUpdateDestroyAPIView, 
    ListCreateAPIView
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    LocationSerializer, 
    MarkerIconSerializer, 
    MarkerSignificanceSerializer
)
from locations.models import Location, MarkerIcon, MarkerSignificance

class CreateUser(APIView):
    """
    View to register/create a new user.
    """
    def post(self, request, format=None):
        """
        Create a new user.

        TODO add additional username/password validation, eg ensuring that
        username consists of only alphanumeric characters.
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
        new_user = get_user_model().objects.create_user(
            username=request.data['username'], 
            password=request.data['password']
        )
        user_token = Token.objects.create(user=new_user)
        return Response({'message': 'User created!', 'token': user_token.key}, status=201)


class LocationsListCreate(ListCreateAPIView):
    """
    View to list all of the user's locations, or
    create new user-bound location.

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

class LocationsRetrieveUpdateDestroy(RetrieveUpdateDestroyAPIView):
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


class MarkerIconsList(ListAPIView):
    """
    View to list all marker icons (these will be the same
    for all users).

    * Requires token authentication.
    """
    queryset= MarkerIcon.objects.all()
    serializer_class = MarkerIconSerializer
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [IsAuthenticated]


class MarkerSignificancesListOrCreate(ListCreateAPIView):
    """
    View to list all of the user's marker significances,
    and significances where owner is set to NULL, or
    create new user-bound significance.

    * Requires token authentication.
    """
    queryset= MarkerSignificance.objects.all()
    serializer_class = MarkerSignificanceSerializer
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def filter_queryset(self, queryset):
        return queryset.filter(Q(owner=self.request.user) | Q(owner__isnull=True))

    def perform_create(self, serializer):
        data = self.request.data
        user_or_null_q = (Q(owner=self.request.user)  | Q(owner__isnull=True))
        label_collision_q = MarkerSignificance.objects.filter(
            user_or_null_q & Q(significance_label=data['significance_label'])
        )
        hex_collision_q = MarkerSignificance.objects.filter(
            user_or_null_q & Q(hex_code=data['hex_code'])
        )
        cname_collision_q = MarkerSignificance.objects.filter(
            user_or_null_q & Q(color_name=data['color_name'])
        )
        if label_collision_q.exists():
            raise ValidationError('Label already in use.')
        if hex_collision_q.exists():
            raise ValidationError('Hex code already in use.')
        if cname_collision_q.exists():
            raise ValidationError('Color name already in use.')
        serializer.save(owner=self.request.user)


class MarkerSignificancesRetrieveUpdateDestroy(RetrieveUpdateDestroyAPIView):
    """
    View to retrieve, update or destroy a single significance.

    * Requires token authentication.
    """
    queryset= MarkerSignificance.objects.all()
    serializer_class = MarkerSignificanceSerializer
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def filter_queryset(self, queryset):
        return queryset.filter(Q(owner=self.request.user) | Q(owner__isnull=True))
