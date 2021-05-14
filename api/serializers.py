from rest_framework.serializers import ModelSerializer, PrimaryKeyRelatedField

from locations.models import (
    Location, 
    MarkerIcon, 
    MarkerSignificance
)


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
    class Meta:
        model = MarkerSignificance
        fields = [
            'id',
            'significance_label',
            'hex_code',
            'color_name'
        ]