import json

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
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    LocationSerializer, 
    MarkerIconSerializer, 
    MarkerSignificanceSerializer,
    ForecastPointSerializer
)
from locations.models import Location, MarkerIcon, MarkerSignificance
from weather.models import ForecastPoint

from .util import colornames
from .util.format import round_coords

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

        # hex codes are to always be saved without an initial '#' symbol
        hex_code = data['hex_code'].replace('#', '').lower()

        # if no color name has been provided, use the colornames library
        # to find the best match
        if ('color_name' not in data) or not data['color_name']:
            color_name = colornames.find('#' + hex_code)
        else:
            color_name = data['color_name']

        user_or_null_q = (Q(owner=self.request.user)  | Q(owner__isnull=True))
        label_collision_q = MarkerSignificance.objects.filter(
            user_or_null_q & Q(significance_label=data['significance_label'])
        )
        hex_collision_q = MarkerSignificance.objects.filter(
            user_or_null_q & Q(hex_code=hex_code)
        )
        cname_collision_q = MarkerSignificance.objects.filter(
            user_or_null_q & Q(color_name=color_name)
        )
        if label_collision_q.exists():
            raise ValidationError('Label already in use.')
        if hex_collision_q.exists():
            raise ValidationError('Hex code already in use.')
        if cname_collision_q.exists():
            raise ValidationError('Color name already in use.')
        serializer.save(owner=self.request.user, hex_code=hex_code, color_name=color_name)


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

class ForecastPointList(APIView):
    """
    View for retrieving forecast point data. Only accepts POST requests,
    whose body should include a JSON array of objects where each object
    is in the format {'lat': 123.4567, 'lon': 123.4567} ie lat/longitude
    coordinates with a maximum of four decimals. Returns a JSON array
    of serialized ForecastPoint instance/entry data, see
    weather.models.ForecastPoint for more information on the model. Note that
    the returned number of points might be less than the number of passed
    coordinate tuples, depending on whether any of the coordinates are
    very close to each other.
    """
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        # print(request.data)
        try:
            coord_ls = request.data['coords']
        except:
            raise ValidationError('Missing required property: coords.')
        print(coord_ls)
        print(type(coord_ls))
        try:
            if not isinstance(coord_ls, list):
                parsed_coord_ls = json.loads(coord_ls)
            else:
                parsed_coord_ls = coord_ls
        except:
            raise ValidationError('coords data format is invalid.')
        print(parsed_coord_ls)
        if not isinstance(parsed_coord_ls, list):
            raise ValidationError('coords must be an array of coordinate objects.')
        rounded_coords = []
        for coord in parsed_coord_ls:
            if ('lat' not in coord) or ('lon' not in coord):
                raise ValidationError("All coordinate objects must have 'lat' and 'lon' properties")
            if abs(coord['lat']) > 90 or abs(coord['lon']) > 180:
                raise ValidationError(f"Invalid coordinates: ({coord['lat']}, {coord['lon']})")
            r_c = round_coords([coord['lat'], coord['lon']], 4)
            rounded_coords.append(r_c)

        match_points = ForecastPoint.update_and_filter(rounded_coords)

        serialized_points = ForecastPointSerializer(match_points, many=True)

        return Response(serialized_points.data, status=201)
