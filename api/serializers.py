from rest_framework.serializers import ModelSerializer, PrimaryKeyRelatedField, CharField

from locations.models import (
    Location, 
    MarkerIcon, 
    MarkerSignificance
)

from weather.models import ForecastPoint


class LocationSerializer(ModelSerializer):
    icon = PrimaryKeyRelatedField(many=False, read_only=False, queryset=MarkerIcon.objects.all())
    significance = PrimaryKeyRelatedField(many=False, read_only=False, queryset=MarkerSignificance.objects.all())

    class Meta:
        model = Location
        fields = [
            'id',
            'place_name', 
            'address', 
            'latitude', 
            'longitude', 
            'business_hours',
            'description',
            'significance',
            'icon',
        ]


class MarkerIconSerializer(ModelSerializer):
    class Meta:
        model = MarkerIcon
        fields = [
            'id',
            'code_name',
            'humanreadable_name'
        ]


class MarkerSignificanceSerializer(ModelSerializer):
    hex_code = CharField(max_length=7, required=True)
    color_name = CharField(required=False, allow_blank=True)

    class Meta:
        model = MarkerSignificance
        fields = [
            'id',
            'significance_label',
            'hex_code',
            'color_name',
            'owner_id'
        ]
        extra_kwargs = {
            'hex_code': {
                'validators': []
            },
        }


class ForecastPointSerializer(ModelSerializer):
    class Meta:
        model = ForecastPoint
        fields = [
            'id',
            'forecast_start_datetime', 
            'latitude', 
            'longitude', 
            'symbol_name_0h',
            't_0h',
            'symbol_name_1h',
            't_1h',
            'symbol_name_2h',
            't_2h',
            'symbol_name_2h',
            't_2h',
            'symbol_name_3h',
            't_3h',
            'symbol_name_4h',
            't_4h',
            'symbol_name_5h',
            't_5h',
            'symbol_name_6h',
            't_6h',
        ]