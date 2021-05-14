from django.test import TestCase
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model

from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from locations.models import Location, MarkerSignificance, MarkerIcon

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
    Note that these rely on basic user creation tests above running correctly.
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
        new_loc = {
            'place_name': 'Jaroslav Jezek Memorial',
            'address': 'Kaprova, Old Town, Prague, Czechia',
            'latitude': 50.08818,
            'longitude': 14.41727,
            'description': 'A memorial',
            'significance': MarkerSignificance.objects.all()[0].id,
            'icon': MarkerIcon.objects.all()[0].id
        }
        resp = self.c.post(
            reverse_lazy('api:locations-lc'),
            new_loc
        )
        self.assertEqual(resp.status_code, 201)

