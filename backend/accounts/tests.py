from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from .models import ADMIN_GROUP, DOCTOR_GROUP, PATIENT_GROUP
from .utils import set_user_group


User = get_user_model()


class AuthAndRBACTests(APITestCase):
    def setUp(self):
        for group_name in (ADMIN_GROUP, DOCTOR_GROUP, PATIENT_GROUP):
            Group.objects.get_or_create(name=group_name)

        self.admin = User.objects.create_user(username="admin", password="Pass12345!", email="admin@test.com")
        set_user_group(self.admin, ADMIN_GROUP)
        self.doctor = User.objects.create_user(username="doctor", password="Pass12345!", email="doctor@test.com")
        set_user_group(self.doctor, DOCTOR_GROUP)
        self.patient = User.objects.create_user(
            username="patient",
            password="Pass12345!",
            email="patient@test.com",
            patient_id="P001",
        )
        set_user_group(self.patient, PATIENT_GROUP)

    def authenticate(self, user):
        token, _ = Token.objects.get_or_create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    def test_signup_creates_patient_user(self):
        response = self.client.post(
            "/api/auth/signup/",
            {
                "username": "newpatient",
                "email": "newpatient@test.com",
                "password": "Pass12345!",
                "first_name": "New",
                "last_name": "Patient",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        user = User.objects.get(username="newpatient")
        self.assertTrue(user.groups.filter(name=PATIENT_GROUP).exists())
        self.assertTrue(user.patient_id.startswith("P"))

    def test_login_returns_token_role_and_dashboard(self):
        response = self.client.post(
            "/api/auth/login/",
            {"username": "doctor", "password": "Pass12345!"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("token", response.data)
        self.assertEqual(response.data["role"], "doctor")
        self.assertEqual(response.data["dashboard"], "doctor")

    def test_patient_cannot_create_doctor(self):
        self.authenticate(self.patient)
        response = self.client.post(
            "/api/admin/doctors/",
            {
                "username": "blockeddoctor",
                "email": "blocked@test.com",
                "password": "Pass12345!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_admin_can_create_patient_with_default_password(self):
        self.authenticate(self.admin)
        response = self.client.post(
            "/api/admin/patients/",
            {
                "username": "adminpatient",
                "email": "adminpatient@test.com",
                "password": "Pass12345!",
                "first_name": "Admin",
                "last_name": "Patient",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        user = User.objects.get(username="adminpatient")
        self.assertTrue(user.groups.filter(name=PATIENT_GROUP).exists())
        self.assertTrue(user.must_change_password)

    def test_listing_doctors_backfills_missing_doctor_id(self):
        self.doctor.doctor_id = None
        self.doctor.save(update_fields=["doctor_id"])

        self.authenticate(self.admin)
        response = self.client.get("/api/admin/doctors/")

        self.assertEqual(response.status_code, 200)
        self.doctor.refresh_from_db()
        self.assertTrue(self.doctor.doctor_id)
        self.assertEqual(response.data[0]["doctor_id"], self.doctor.doctor_id)
