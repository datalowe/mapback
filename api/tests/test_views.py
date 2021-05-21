import json

from django.test import TestCase
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model

from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from locations.models import Location, MarkerSignificance, MarkerIcon
from weather.models import ForecastPoint

class CreateUserTestCase(TestCase):
    """
    Tests for the CreateUser CBV.
    """
    def setUp(self):
        self.c = APIClient()
        self.reg_url = reverse_lazy('api:create-user')
        self.u1_data = {'username': 'starr', 'password': '111django111'}
        self.u2_data = {'username': 'lennon', 'password': '111django111'}

    def test_valid_user_creation(self):
        """
        Creating a user with valid (>2 char username, >5 char password)
        updates database and returns 201 status code response.
        """
        # resp = self.c.post(self.reg_url, self.u1_data)
        resp = self.c.post(self.reg_url, {'username': 'starr', 'password': '111django111'})
        # responded with status code 201 created
        self.assertEqual(resp.status_code, 201)
        # user created
        self.assertTrue(
            get_user_model().objects.filter(username=self.u1_data['username']).exists()
        )

    def test_tooshort_password(self):
        """
        Attempting to create user with a too short password provokes error response.
        """
        resp = self.c.post(self.reg_url, {'username': 'foobar', 'password': '00'})
        # status code 400 bad request
        self.assertEqual(resp.status_code, 400)
    
    def test_tooshort_username(self):
        """
        Attempting to create user with a too short username provokes error response.
        """
        resp = self.c.post(self.reg_url, {'username': 'fo', 'password': '111django111'})
        # status code 400 bad request
        self.assertEqual(resp.status_code, 400)
    
    def test_missing_username(self):
        """
        Attempting to create user without a username provokes error response.
        """
        resp = self.c.post(self.reg_url, {'password': '111django111'})
        # status code 400 bad request
        self.assertEqual(resp.status_code, 400)
    
    def test_missing_password(self):
        """
        Attempting to create user without a password provokes error response.
        """
        resp = self.c.post(self.reg_url, {'username': 'foobar'})
        # status code 400 bad request
        self.assertEqual(resp.status_code, 400)
    
    def test_preexisting_username(self):
        """
        Attempting to create user with a username already taken provokes error response.
        """
        self.c.post(self.reg_url, self.u1_data)
        resp = self.c.post(self.reg_url, self.u1_data)
        # status code 409 conflict
        self.assertEqual(resp.status_code, 409)


class ActAsUserTestCase(TestCase):
    """
    Integration tests where a user logs in and interacts with the API.
    
    * Note that these rely on basic user creation tests above running correctly.
    """
    def setUp(self):
        self.c = APIClient()
        self.auth_url = reverse_lazy('api:obtain-auth-token')
        # uses a preexisting user, which is created in 'fixture migration'
        # in 'locations/migrations/0002_insertdata_20210512_0747.py'
        self.test_user = get_user_model().objects.get(username='lowe')
        self.test_user_token = Token.objects.create(user=self.test_user)
        self.test_user_2 = get_user_model().objects.get(username='regular')
        self.test_user_2_token = Token.objects.create(user=self.test_user_2)
        self.add_loc = {
            'place_name': 'Jaroslav Jezek Memorial',
            'address': 'Kaprova, Old Town, Prague, Czechia',
            'latitude': 50.08818,
            'longitude': 14.41727,
            'description': 'A memorial',
            'significance': MarkerSignificance.objects.all()[0].id,
            'icon': MarkerIcon.objects.all()[0].id
        }
        self.add_sig = {
            'significance_label': 'Added significance',
            'hex_code': '101010',
            'color_name': 'addcolor'
        }
        self.test_user_significance = MarkerSignificance.objects.create(
            significance_label='If nothing to do',
            hex_code='808080',
            color_name='boring-grey',
            owner=self.test_user
        )
        self.test_user_2_significance = MarkerSignificance.objects.create(
            significance_label='BBQ place - only the best',
            hex_code='ffa030',
            color_name='flamy',
            owner=self.test_user_2
        )

    def tearDown(self):
        self.c.credentials()

    def test_get_user_token_valid(self):
        """
        Hitting token endpoint with valid credentials returns a token
        even for a brand new user.
        """
        reg_url = reverse_lazy('api:create-user')
        user_data = {'username': 'Harrison', 'password': '111django111'}
        self.c.post(reg_url, user_data)
        resp = self.c.post(self.auth_url, user_data)
        self.assertIn('token', resp.data)
    
    def test_get_user_token_invalid(self):
        """
        Hitting token endpoint with invalid credentials 
        provokes an error response.
        """
        user_data = {'username': 'nonexistent', 'password': 'passpass'}
        resp = self.c.post(self.auth_url, user_data)
        self.assertNotIn('token', resp.data)
        self.assertEqual(resp.status_code, 400)
    
    def test_get_locations_valid_credentials(self):
        """
        Visiting the locations list endpoint with
        valid credentials returns a response
        which includes all of the user's locations.
        """
        self.c.credentials(HTTP_AUTHORIZATION='Token ' + self.test_user_token.key)
        resp = self.c.get(
            reverse_lazy('api:locations-lc'), 
        )
        self.assertEqual(resp.status_code, 200)
        # response returned as many objects as there are
        # locations owned by the user in the database
        self.assertEqual(
            Location.objects.filter(owner=self.test_user).count(),
            len(resp.data)
        )

    def test_get_locations_no_credentials(self):
        """
        Visiting the locations list endpoint without
        a token returns a 403 response.
        """
        resp = self.c.get(
            reverse_lazy('api:locations-lc'), 
        )
        self.assertEqual(resp.status_code, 401)
    
    def test_get_locations_invalid_credentials(self):
        """
        Visiting the locations list endpoint without
        an invalid token returns a 403 response.
        """
        self.c.credentials(HTTP_AUTHORIZATION='Token invalid_token')
        resp = self.c.get(
            reverse_lazy('api:locations-lc'), 
        )
        self.assertEqual(resp.status_code, 401)
    
    def test_get_location_valid_credentials(self):
        """
        Visiting the location R/U/D endpoint with
        valid credentials returns a response
        which includes the location data.
        """
        self.c.credentials(HTTP_AUTHORIZATION='Token ' + self.test_user_token.key)
        valid_loc = Location.objects.filter(owner=self.test_user)[0]
        resp = self.c.get(
            reverse_lazy('api:locations-rud', kwargs={'pk': valid_loc.id}), 
        )
        self.assertEqual(resp.status_code, 200)
        # response returned a single location, with the correct
        # place name
        self.assertEqual(
            resp.data['place_name'],
            valid_loc.place_name
        )
    
    def test_get_location_invalid_credentials(self):
        """
        Visiting the location R/U/D endpoint with
        valid credentials, but requesting
        a location which does not belong to the user,
        provokes an error response.
        """
        self.c.credentials(HTTP_AUTHORIZATION='Token ' + self.test_user_2_token.key)
        invalid_loc = Location.objects.filter(owner=self.test_user)[0]
        resp = self.c.get(
            reverse_lazy('api:locations-rud', kwargs={'pk': invalid_loc.id}), 
        )
        self.assertEqual(resp.status_code, 404)

    def test_create_location_valid_credentials(self):
        """
        Creating a location with valid data creates new
        database record and returns created status code.
        """
        self.c.credentials(HTTP_AUTHORIZATION='Token ' + self.test_user_token.key)

        resp = self.c.post(
            reverse_lazy('api:locations-lc'),
            self.add_loc
        )
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(
            Location.objects.filter(place_name=self.add_loc['place_name']).exists()
        )

    def test_delete_location_valid_credentials(self):
        """
        Deleting a location with valid credentials updates
        database and returns 'no content' status code.

        * Note that this test relies on above 'creation' test already working.
        """
        self.c.credentials(HTTP_AUTHORIZATION='Token ' + self.test_user_token.key)
        resp_create = self.c.post(
            reverse_lazy('api:locations-lc'),
            self.add_loc
        )
        resp_delete = self.c.delete(
            reverse_lazy('api:locations-rud', kwargs={'pk': resp_create.data['id']})
        )
        self.assertEqual(resp_delete.status_code, 204)
        self.assertFalse(
            Location.objects.filter(place_name=self.add_loc['place_name']).exists()
        )
    
    def test_delete_location_wrong_user(self):
        """
        Trying to delete another user's location produces a 404 error response.

        * Note that this test relies on above 'creation' test already working.
        """
        self.c.credentials(HTTP_AUTHORIZATION='Token ' + self.test_user_token.key)
        resp_create = self.c.post(
            reverse_lazy('api:locations-lc'),
            self.add_loc
        )
        self.c.credentials(HTTP_AUTHORIZATION='Token ' + self.test_user_2_token.key)
        resp_delete = self.c.delete(
            reverse_lazy('api:locations-rud', kwargs={'pk': resp_create.data['id']})
        )
        self.assertEqual(resp_delete.status_code, 404)

    def test_update_location_valid_credentials(self):
        """
        Updating a location with valid credentials updates
        database and produces 200 status code response.

        * Note that this test relies on above 'creation' test already working.
        """
        self.c.credentials(HTTP_AUTHORIZATION='Token ' + self.test_user_token.key)
        resp_create = self.c.post(
            reverse_lazy('api:locations-lc'),
            self.add_loc
        )
        updated_loc = {x:y for x,y in self.add_loc.items()}
        updated_loc['description'] = 'updated description'
        resp_put = self.c.put(
            reverse_lazy('api:locations-rud', kwargs={'pk': resp_create.data['id']}),
            updated_loc
        )
        self.assertEqual(resp_put.status_code, 200)
        self.assertTrue(
            Location.objects.filter(description=updated_loc['description']).exists()
        )

    def test_get_icons_valid_credentials(self):
        """
        Visiting the icons list endpoint with
        valid credentials returns a response
        which includes all of the user's locations.
        """
        self.c.credentials(HTTP_AUTHORIZATION='Token ' + self.test_user_token.key)
        resp = self.c.get(
            reverse_lazy('api:markericons-l'), 
        )
        self.assertEqual(resp.status_code, 200)
        # response returned as many objects as there are
        # locations owned by the user in the database
        self.assertEqual(
            MarkerIcon.objects.count(),
            len(resp.data)
        )
    
    def test_get_significances_valid_credentials(self):
        """
        Visiting the marker significances list endpoint with
        valid credentials returns a response
        which includes all of the user's significances,
        as well as significances with owner set to NULL.
        """
        self.c.credentials(HTTP_AUTHORIZATION='Token ' + self.test_user_token.key)
        resp = self.c.get(
            reverse_lazy('api:markersignificances-lc'), 
        )
        self.assertEqual(resp.status_code, 200)
        # response returned as many objects as there are
        # locations owned by the user in the database
        self.assertEqual(
            MarkerSignificance.objects.filter(owner=self.test_user).count() +
            MarkerSignificance.objects.filter(owner__isnull=True).count(),
            len(resp.data)
        )

    def test_create_significance_valid_credentials(self):
        """
        Creating a significance with valid data creates new
        database record and returns created status code.
        """
        self.c.credentials(HTTP_AUTHORIZATION='Token ' + self.test_user_token.key)

        resp = self.c.post(
            reverse_lazy('api:markersignificances-lc'), 
            self.add_sig
        )
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(
            MarkerSignificance.objects.filter(
                significance_label=self.add_sig['significance_label']
            ).exists()
        )

    def test_create_significance_excluding_colorname(self):
        """
        Creating a significance with valid data, excluding
        color name (or leaving it blank), creates new
        database record where color hex code has been used
        to produce appropriate color name.
        """
        self.c.credentials(HTTP_AUTHORIZATION='Token ' + self.test_user_token.key)

        add_sig_1 = {
            'significance_label': 'Added significance 1',
            # colorpicker library name: 'Dune'
            'hex_code': '3e3e3e'
        }

        add_sig_2 = {
            'significance_label': 'Added significance 2',
            # colorpicker library name: 'Wild Sand'
            'hex_code': '#f5f5f5'
        }

        add_sig_3 = {
            'significance_label': 'Added significance 3',
            # colorpicker library name: 'Jaffa'
            'hex_code': '#f88333',
            'color_name': ''
        }

        resp1 = self.c.post(
            reverse_lazy('api:markersignificances-lc'), 
            add_sig_1
        )

        resp2 = self.c.post(
            reverse_lazy('api:markersignificances-lc'), 
            add_sig_2
        )

        resp3 = self.c.post(
            reverse_lazy('api:markersignificances-lc'), 
            add_sig_3
        )

        self.assertEqual(resp1.status_code, 201)
        self.assertEqual(resp2.status_code, 201)
        self.assertEqual(resp3.status_code, 201)
        self.assertTrue(
            MarkerSignificance.objects.filter(
                color_name='Dune'
            ).exists()
        )
        self.assertTrue(
            MarkerSignificance.objects.filter(
                color_name='Wild Sand'
            ).exists()
        )
        self.assertTrue(
            MarkerSignificance.objects.filter(
                color_name='Jaffa'
            ).exists()
        )

    def test_create_significance_duplicate_label(self):
        """
        Attempting to create a significance with a label
        already used by one of user's significances 
        provokes an error response.
        """
        self.c.credentials(HTTP_AUTHORIZATION='Token ' + self.test_user_token.key)

        dup_sig = {x:y for x,y in self.add_sig.items()}
        dup_sig['significance_label'] = self.test_user_significance.significance_label

        resp = self.c.post(
            reverse_lazy('api:markersignificances-lc'), 
            dup_sig
        )
        self.assertEqual(resp.status_code, 400)

    def test_delete_significance_valid_credentials(self):
        """
        Deleting a significance with valid credentials updates
        database and returns 'no content' status code.

        * Note that this test relies on above 'creation' test already working.
        """
        self.c.credentials(HTTP_AUTHORIZATION='Token ' + self.test_user_token.key)
        resp_create = self.c.post(
            reverse_lazy('api:markersignificances-lc'),
            self.add_sig
        )
        resp_delete = self.c.delete(
            reverse_lazy('api:markersignificances-rud', 
            kwargs={'pk': resp_create.data['id']})
        )
        self.assertEqual(resp_delete.status_code, 204)
        self.assertFalse(
            MarkerSignificance.objects.filter(
                significance_label=self.add_sig['significance_label']
            ).exists()
        )


class ForecastPointListTestCase(TestCase):
    """
    Integration tests where a user logs in and gets weather data from API.
    
    * Note that these rely on basic user creation tests above running correctly.
    """
    def setUp(self):
        self.c = APIClient()
        self.auth_url = reverse_lazy('api:obtain-auth-token')
        # uses a preexisting user, which is created in 'fixture migration'
        # in 'locations/migrations/0002_insertdata_20210512_0747.py'
        self.test_user = get_user_model().objects.get(username='lowe')
        self.test_user_token = Token.objects.create(user=self.test_user)
        self.retrieve_coords = {
            'coords': 
                [
                    {"lat": 59.3293235, "lon": 18.0685808}, 
                    {"lat": 57.7, "lon": 11.9666666667}
                ]
        }

    def tearDown(self):
        self.c.credentials()
    
    # DISABLED usually, to avoid making unnecessary calls to weather API
    # def test_get_weather_data(self):
    #     """
    #     Retrieving weather data for two sets of previously unregistered coordinates 
    #     adds two entries to forecast points table.
    #     """
    #     pre_num_forecastpoints = ForecastPoint.objects.count()
    #     self.c.credentials(HTTP_AUTHORIZATION='Token ' + self.test_user_token.key)
    #     # default django test client JSON formatting doesn't work here, so we
    #     # need to do it manually
    #     resp = self.c.post(
    #         reverse_lazy('api:forecasts-l'),
    #         data=json.dumps(self.retrieve_coords),
    #         content_type='application/json'
    #     )
    #     # print(resp.data)
    #     self.assertEqual(resp.status_code, 201)
    #     post_num_forecastpoints = ForecastPoint.objects.count()
    #     self.assertEqual(pre_num_forecastpoints + len(self.retrieve_coords['coords']), post_num_forecastpoints)
