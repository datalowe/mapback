import requests

from datetime import datetime

from pytz import UTC

DEFAULT_USER_AGENT = "MyMap https://github.com/datalowe/mymap datalowe@posteo.de"

YR_API_ENDPOINT = "https://api.met.no/weatherapi/locationforecast/2.0/compact"

YR_DATE_FORMAT_SPEC = '%Y-%m-%dT%H:%M:%SZ'

HEADER_DATE_FORMAT_SPEC = "%a, %d %b %Y %H:%M:%S GMT"

def strptime_with_utc(time_str, format_spec):
    """
    Takes in a string that describes a timepoint and which is to be
    parsed, and a format specification string which says how the
    timepoint string is formatted. Returns the parsed time
    as a datetime object, with UTC set as the timezone.
    """
    naive_dt = datetime.strptime(time_str, format_spec)
    aware_dt = naive_dt.astimezone(UTC)
    return aware_dt

def get_forecast(lat, lon, if_modified_since = None, user_agent=None):
    """
    Queries the YR weather api and returns subset of data.
    :param lat: float - Latitude, as a four-decimal value.
    :param lon: float - Longitude, as a four-decimal value.
    :param if_modified_since: datetime - Describes (in UTC)
    datetime after which forecast must have been updated for updated
    data to be returned by API.
    :param user_agent: (optional) str - String to include as
    value for 'User-Agent' header.
    :return: dict - Has the following keys:
    forecast_start_datetime
    last_forecast_update_datetime
    new_req_allowed_datetime
    latitude
    longitude
    symbol_name_0h
    t_0h
    symbol_name_1h
    ...
    symbol_name_6h
    t_6h
    (see ForecastPoint model for info on these)
    """

    if user_agent is None:
        user_agent = DEFAULT_USER_AGENT
    headers = {
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "User-Agent": user_agent
    }
    if if_modified_since:
        modified_str = if_modified_since.strftime(HEADER_DATE_FORMAT_SPEC)
        headers["If-Modified-Since"] = modified_str
    resp = requests.get(
        YR_API_ENDPOINT,
        params = {
            "lat": lat,
            "lon": lon,
        },
        headers = headers
    )
    return_data = {}
    resp_json = resp.json()
    resp_props = resp_json['properties']
    resp_ts = resp_props['timeseries']

    return_data['last_forecast_update_datetime'] = strptime_with_utc(
        resp_props['meta']['updated_at'], YR_DATE_FORMAT_SPEC
    )

    return_data['forecast_start_datetime'] = strptime_with_utc(
        resp_ts[0]['time'], YR_DATE_FORMAT_SPEC
    )

    return_data['new_req_allowed_datetime'] = strptime_with_utc(
        resp.headers['Expires'], HEADER_DATE_FORMAT_SPEC
    )

    return_data['latitude'] = resp_json['geometry']['coordinates'][1]
    return_data['longitude'] = resp_json['geometry']['coordinates'][0]

    for i in range(7):
        ts_data = resp_ts[i]['data']
        return_data[f'symbol_name_{i}h'] = ts_data['next_1_hours']['summary']['symbol_code']
        return_data[f't_{i}h'] = ts_data['instant']['details']['air_temperature']

    return return_data
