import random

from django.test import TestCase

from ..api_request_functions.yr_api import get_forecast


class YrApiTestCase(TestCase):
    """
    Tests of YR API request functions.
    """
    @staticmethod
    def get_rand_coord():
        return round(random.choice([-1, 1]) * random.random() * 90, 4)
    
    # DISABLED usually, to keep from making unneccessary requests to YR API
    # def test_get_forecast(self):
    #     lat = YrApiTestCase.get_rand_coord()
    #     lon = YrApiTestCase.get_rand_coord()
    #     resp = get_forecast(lat, lon)
    #     self.assertTrue('new_req_allowed_datetime' in resp)