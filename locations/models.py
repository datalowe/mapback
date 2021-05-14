from django.db import models
from django.urls import reverse_lazy
from django.contrib.auth.models import User
from django.utils import timezone

SHORTENED_LENGTH = 20

class MarkerIcon(models.Model):
    """
    Represents icons, to be used as map markers.
    Note that no references to actual images are included in
    this representation, only names of icons. Front-ends using
    this model are responsible for translating icon names into
    concrete icons/images.
    """
    # a concise icon name, eg 'utensils', or 'shopping'
    code_name = models.CharField(max_length=50, unique=True)
    # a human-readable name (in English), which is to be used in
    # interfaces presented to users, eg 'utensils' or 'shopping bag'
    humanreadable_name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return f'{self.humanreadable_name} ({self.code_name})'

class MarkerSignificance(models.Model):
    """
    Represents 'significance' of map markers, eg if a location
    is a high priority destination or if a location is 
    somewhere a traveller plans to stay for a night.
    """
    # a concise 
    # a label that describes a marker's significance,
    # eg "definitely visit" or "visit if there's time"
    significance_label = models.CharField(max_length=20, unique=True)
    # hex code of default color that corresponds to significance. 
    # note that hex codes do not include a pound sign, so
    # instead of '#f0abcd', one would store 'f0abcd'
    hex_code = models.CharField(max_length=6, unique=True)
    # a human readable color name, eg 'fuchsia' or
    # 'light yellow'
    color_name = models.CharField(max_length=20, unique=True)
    # significances are linked to users, except default
    # significances where the user is set to NULL
    owner = models.ForeignKey(User, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.significance_label} ({self.color_name})'

class Location(models.Model):
    """
    Represents a geographical location.
    """
    # users are expected to insert at least either a place name or an
    # address
    place_name = models.CharField(max_length=200, blank=True, null=True)
    address = models.CharField(max_length=200, blank=True, null=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=7)
    longitude = models.DecimalField(max_digits=10, decimal_places=7)
    # business hours is registered as a plain varchar field, since
    # the user might want to input additional info about eg holiday
    # business hours
    business_hours = models.CharField(max_length=200, blank=True, null=True)
    description = models.CharField(max_length=500, blank=True, null=True)
    significance = models.ForeignKey(MarkerSignificance, on_delete=models.CASCADE)
    icon = models.ForeignKey(MarkerIcon, on_delete=models.CASCADE)
    # a location is always linked to a single user
    owner = models.ForeignKey(User, null=True, on_delete=models.CASCADE)

    def __str__(self):
        if self.place_name:
            return self.place_name
        if self.address:
            return self.address
        return f'Location at: ({self.latitude}, {self.longitude})'
        

    class Meta:
        ordering = ['place_name']

    def place_name_shortened(self):
        if not self.place_name:
            return 'Has no place name'
        if len(self.place_name) > SHORTENED_LENGTH:
            return self.place_name[:SHORTENED_LENGTH] + '...'
        return self.place_name

    def latitude_shortened(self):
        return round(self.latitude, 2)

    def longitude_shortened(self):
        return round(self.longitude, 2)

    def business_hours_shortened(self):
        if not self.business_hours:
            return 'Has no business hours'
        if len(self.business_hours) > SHORTENED_LENGTH:
            return self.business_hours[:SHORTENED_LENGTH] + '...'
        return self.business_hours

    def description_shortened(self):
        if not self.description:
            return 'Has no business hours'
        if len(self.description) > SHORTENED_LENGTH:
            return self.description[:SHORTENED_LENGTH] + '...'
        return self.description

    def get_absolute_url(self):
        return reverse_lazy('locations:location-detail', kwargs={'pk': self.pk})


class VisitedGeoPosition(models.Model):
    """
    Represents a geographical position where a user has been. 
    This is meant to be used for tracking trips. For instance, 
    a front-end might send updates every minute or 15 minutes about
    user position, triggering a new VisitedGeoPosition instance/entry.
    """
    latitude = models.DecimalField(max_digits=10, decimal_places=7)
    longitude = models.DecimalField(max_digits=10, decimal_places=7)
    # UTC timestamps are always saved for visited geographical positions,
    # to ensure that the user's chain of visited positions can be
    # illustrated in a chronologically correct fashion, even if the
    # user would eg cross over a timezone border. to enable
    # saving geographical positions at a later time (eg front-end
    # caches positions while user is offline), an explicit value
    # to save can be provided here, overriding the default
    utc_timestamp = models.DateTimeField(default=timezone.now)
    # 'wall clock' timestamps can be used by a front-end to
    # show users at what time (according to their device at the time) 
    # they visited a position. these are normally expected to be 
    # provided by a front-end, to make sure that users' 
    # device timezone settings are respected.
    # note that the times are still saved as 'UTC', but are really
    # values for specific timezones.
    # front-ends can however skip offering this functionality and 
    # safely ignore this field
    wall_clock_timestamp = models.DateTimeField(default=None, null=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f'({self.latitude}, {self.longitude}), visited at {self.utc_timestamp} by {self.owner}'
