from datetime import datetime

from pytz import UTC

from django.test import TestCase

from ..models import ForecastPoint


class ForecastPointTestCase(TestCase):
    """
    Tests of ForecastPoint class.
    """

    # DISABLED usually, to keep from making unneccessary requests to YR API.
    # relies on the database migration '0002_insertdata_2021...' having been run
    # def test_sync_with_api(self):
    #     fp = ForecastPoint.objects.all()[0]

    #     fp.sync_with_api()

    #     utc_mock_now = datetime.now().astimezone(UTC)

    #     diff_time = abs((utc_mock_now - fp.forecast_start_datetime).total_seconds())

    #     # check that the difference between current time and fetched data's start time is
    #     # less than 48 hours
    #     self.assertLessEqual(diff_time, 3600 * 48)

    # DISABLED usually, to keep from making unneccessary requests to YR API.
    # relies on the database migration '0002_insertdata_2021...' having been run
    # def test_update_and_filter_onlypreexisting(self):
    #     """
    #     update_and_filter method returns correct results when passed coordinates for which there already are
    #     database entries, and updates database entries.
    #     """
    #     res = ForecastPoint.update_and_filter([(-59.3103, -14.4888), (-5.8100, -3.0000)])
    #     self.assertEqual(len(res), 2)

    #     fp = ForecastPoint.objects.all()[1]

    #     utc_mock_now = datetime.now().astimezone(UTC)
    #     diff_time = abs((utc_mock_now - fp.forecast_start_datetime).total_seconds())
    #     self.assertLessEqual(diff_time, 3600 * 48)
