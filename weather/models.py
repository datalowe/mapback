from django.db import models
from django.db.models import Q
from django.utils import timezone

from .api_request_functions.yr_api import get_forecast

class ForecastPoint(models.Model):
    """
    Represents forecasts for geographical locations.
    """
    # date/time (UTC) which corresponds to 0h forecast data
    # (eg if '2021-03-01 20:30' datetime is stored here, and first
    # temperature value is 20, then it's forecasted that
    # the temperature at the lat/lon coordinates is 20 Celsius
    # at 2021-03-01 20:30, UTC time)
    forecast_start_datetime = models.DateTimeField()

    # date/time (UTC) at which the forecast for the location
    # was updated (eg in YR weather API responses, this is sent
    # as the 'Last-Modified' header)
    last_forecast_update_datetime = models.DateTimeField()

    # date/time (UTC) at which the weather API allows a request
    # for updated forecast information for location
    # (eg in YR weather API responses, this is sent as
    # the 'Expires' header)
    new_req_allowed_datetime = models.DateTimeField()

    # location latitude/longitude - __uses only__ 4 decimals, since
    # it doesn't make sense/only adds data load to
    # include more fine-grained forecast areas
    # (and in YR weather API's case, they forbid requesting
    # more fine-grained data than 4)
    latitude = models.DecimalField(max_digits=7, decimal_places=4)
    longitude = models.DecimalField(max_digits=7, decimal_places=4)

    # name of weather icon that represents the weather state at 0h
    # from 
    # (eg in YR weather API, 'symbol_code' values like 'partlycloudy_day'
    # are used)
    symbol_name_0h = models.CharField(max_length=50)
    # forecasted temperature for same timepoint
    t_0h = models.DecimalField(max_digits=4, decimal_places=1)

    # there is a lot of redundancy below - an alternative would
    # be to create a separate model for symbol names and temperatures,
    # linked to this one with a foreign key. this would require adding
    # functionality for updating entries in this related model
    symbol_name_1h = models.CharField(max_length=50)
    t_1h = models.DecimalField(max_digits=4, decimal_places=1)

    symbol_name_2h = models.CharField(max_length=50)
    t_2h = models.DecimalField(max_digits=4, decimal_places=1)

    symbol_name_3h = models.CharField(max_length=50)
    t_3h = models.DecimalField(max_digits=4, decimal_places=1)

    symbol_name_4h = models.CharField(max_length=50)
    t_4h = models.DecimalField(max_digits=4, decimal_places=1)

    symbol_name_5h = models.CharField(max_length=50)
    t_5h = models.DecimalField(max_digits=4, decimal_places=1)

    symbol_name_6h = models.CharField(max_length=50)
    t_6h = models.DecimalField(max_digits=4, decimal_places=1)

    def __str__(self):
        return f'Forecast point at ({self.latitude}, {self.longitude})'

    @classmethod
    def update_and_filter(cls, coord_ls):
        """
        Accepts a list of geographical coordinates. For each one, checks if
        there is a corresponding ForecastPoint entry already. Where there
        is none, a request to the weather API is made and a new entry is
        created. For entries where the forecast data are >1h old, and the time
        for when a new API request is allowed has passed, entries are updated
        by requesting new data from the weather API.
        :param coord_ls: A list of 2-element float tuples, where the first
        value represents a latitude, and the second a longitude.
        :return: A list of ForecastPoint instances
        """
        # check if an empty list was passed
        if not coord_ls:
            return []

        # 1) round all passed coordinates to 4 decimals
        coord_ls = [(round(lat, 4), round(lon, 4)) for lat, lon in coord_ls]

        # 2) form a large query object, essentially a chain of OR checks for
        # latitude/longitude pairs
        super_q = Q(latitude=coord_ls[0][0]) & Q(longitude=coord_ls[0][1])

        for coord in coord_ls[1:]:
            super_q |= Q(latitude=coord_ls[0][0]) & Q(longitude=coord_ls[0][1])

        # 3) filter by all coordinates and force evaluation of the resulting queryset
        match_points = list(cls.objects.filter(super_q))

        # 4) form a list of returned database entries' coordinates
        db_coords = [(float(p.latitude), float(p.longitude)) for p in match_points]

        # 5) update database entries which are out of sync with weather API
        for p in match_points:
            if p.time_to_sync():
                p.sync_with_api()
        
        # 6) check if all passed coordinates (coord_ls) occur in list formed in step 4,
        # and for any coordinates for which there is no matching database entry,
        # create a new instance/entry by using weather API
        for coord in coord_ls:
            if coord not in db_coords:
                new_point = cls.create_with_api(*coord)
                match_points.append(new_point)
        
        return match_points
    
    @classmethod
    def create_with_api(cls, lat, lon, api_getter=get_forecast):
        """
        Takes in lat/longitude coordinates, fetches corresponding data from weather API,
        and uses the data to form a new instance/database entry.
        :returns: A ForecastPoint instance, referencing the newly created database entry.
        """
        api_results = api_getter(lat=lat, lon=lon)
        return cls.objects.create(**api_results)

    def sync_with_api(self, api_getter=get_forecast):
        """
        Requests updated forecast data from API service and updates
        the points corresponding database entry accordingly.
        :param api_getter: function - See .api_request_functions.yr_api.get_forecast
        for an example which explains expected interface/output.
        """
        api_results = api_getter(
            lat=self.latitude, 
            lon=self.longitude, 
            if_modified_since=self.last_forecast_update_datetime,
        )
        self.forecast_start_datetime = api_results['forecast_start_datetime']
        self.last_forecast_update_datetime = api_results['last_forecast_update_datetime']
        self.new_req_allowed_datetime = api_results['new_req_allowed_datetime']
        self.symbol_name_0h = api_results['symbol_name_0h']
        self.t_0h = api_results['t_0h']
        self.symbol_name_1h = api_results['symbol_name_1h']
        self.t_1h = api_results['t_1h']
        self.symbol_name_2h = api_results['symbol_name_2h']
        self.t_2h = api_results['t_2h']
        self.symbol_name_3h = api_results['symbol_name_3h']
        self.t_3h = api_results['t_3h']
        self.symbol_name_4h = api_results['symbol_name_4h']
        self.t_5h = api_results['t_5h']
        self.symbol_name_6h = api_results['symbol_name_6h']
        self.t_6h = api_results['t_6h']
        self.save()

    def time_to_sync(self):
        """
        Checks datetime information to see if it's time to update the database entry by
        synchronizing with the weather API being used. Currently this checks if
        the current time is >30 minutes past the 'forecast_start_datetime' _and_
        the current time is past the 'new_req_allowed_datetime'
        """
        # note that this assumes that the Django project is configured with USE_TZ=True
        # and TIME_ZONE='UTC'
        current_utc = timezone.now()
        delta_since_start_time = current_utc - self.forecast_start_datetime
        is_time = delta_since_start_time.total_seconds() > 1800
        is_allowed = current_utc > self.new_req_allowed_datetime
        return is_time and is_allowed
