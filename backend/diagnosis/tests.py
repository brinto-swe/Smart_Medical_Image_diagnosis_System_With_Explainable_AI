from unittest.mock import patch

import numpy as np
import shutil
import tempfile
from datetime import datetime, time, timedelta
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from accounts.models import ADMIN_GROUP, DOCTOR_GROUP, PATIENT_GROUP
from accounts.utils import set_user_group

from .models import DoctorAssignment, ScanResult


User = get_user_model()


class DiagnosisFlowTests(APITestCase):
    def setUp(self):
        self.temp_media_root = tempfile.mkdtemp()
        self.settings_override = self.settings(MEDIA_ROOT=self.temp_media_root)
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        self.addCleanup(shutil.rmtree, self.temp_media_root, ignore_errors=True)

        for group_name in (ADMIN_GROUP, DOCTOR_GROUP, PATIENT_GROUP):
            Group.objects.get_or_create(name=group_name)

        self.doctor = User.objects.create_user(username="doctor", password="Pass12345!", doctor_id="D001")
        set_user_group(self.doctor, DOCTOR_GROUP)
        self.admin = User.objects.create_user(username="admin", password="Pass12345!")
        set_user_group(self.admin, ADMIN_GROUP)
        self.patient = User.objects.create_user(username="patient", password="Pass12345!", patient_id="P001")
        set_user_group(self.patient, PATIENT_GROUP)

    def authenticate(self, user):
        token, _ = Token.objects.get_or_create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    def test_doctor_can_search_patients(self):
        self.authenticate(self.doctor)
        response = self.client.get("/api/doctor/patients/search/?q=P001")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["patient_id"], "P001")

    @patch("diagnosis.views.predict")
    def test_doctor_upload_saves_scan_result(self, mock_predict):
        self.authenticate(self.doctor)
        mock_predict.return_value = {
            "prediction": "NORMAL",
            "confidence": 0.95,
            "risk_level": "LOW",
            "heatmap": np.zeros((10, 10, 3), dtype=np.uint8),
        }
        image = SimpleUploadedFile("xray.jpg", b"fake-image", content_type="image/jpeg")

        response = self.client.post(
            "/api/doctor/xray/upload/",
            {"patient_id": "P001", "image": image},
            format="multipart",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(ScanResult.objects.count(), 1)
        scan = ScanResult.objects.get()
        self.assertEqual(scan.patient, self.patient)
        self.assertEqual(scan.uploaded_by, self.doctor)

    def test_patient_sees_only_own_reports(self):
        other = User.objects.create_user(username="other", password="Pass12345!", patient_id="P002")
        set_user_group(other, PATIENT_GROUP)
        ScanResult.objects.create(
            patient=self.patient,
            uploaded_by=self.doctor,
            original_image=SimpleUploadedFile("one.jpg", b"one", content_type="image/jpeg"),
            prediction="NORMAL",
            confidence=0.9,
            risk_level="LOW",
        )
        ScanResult.objects.create(
            patient=other,
            uploaded_by=self.doctor,
            original_image=SimpleUploadedFile("two.jpg", b"two", content_type="image/jpeg"),
            prediction="PNEUMONIA",
            confidence=0.9,
            risk_level="HIGH",
        )

        self.authenticate(self.patient)
        response = self.client.get("/api/scans/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["patient_id"], "P001")

    def test_admin_can_assign_doctor_to_patient(self):
        self.authenticate(self.admin)
        scheduled_at = (timezone.now() + timedelta(days=1)).replace(microsecond=0)
        response = self.client.post(
            "/api/admin/assignments/",
            {
                "patient_id": "P001",
                "doctor_id": self.doctor.doctor_id or "D001",
                "scheduled_at": scheduled_at.isoformat(),
                "notes": "Follow-up chest scan",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["patient_id"], "P001")
        self.assertEqual(response.data["doctor_name"], self.doctor.username)
        self.assertEqual(DoctorAssignment.objects.count(), 1)

    def test_doctor_sees_only_own_assigned_patients(self):
        second_doctor = User.objects.create_user(username="doctor2", password="Pass12345!", doctor_id="D002")
        set_user_group(second_doctor, DOCTOR_GROUP)
        other_patient = User.objects.create_user(username="patient2", password="Pass12345!", patient_id="P002")
        set_user_group(other_patient, PATIENT_GROUP)
        today = timezone.localdate()
        DoctorAssignment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            assigned_by=self.admin,
            scheduled_at=timezone.make_aware(datetime.combine(today, time(hour=10))),
        )
        DoctorAssignment.objects.create(
            patient=other_patient,
            doctor=second_doctor,
            assigned_by=self.admin,
            scheduled_at=timezone.make_aware(datetime.combine(today, time(hour=11))),
        )

        self.authenticate(self.doctor)
        response = self.client.get(f"/api/doctor/assignments/?date={today.isoformat()}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["patient_id"], "P001")

    def test_analytics_endpoint_is_admin_only_and_returns_chart_data(self):
        self.authenticate(self.admin)
        ScanResult.objects.create(
            patient=self.patient,
            uploaded_by=self.doctor,
            original_image=SimpleUploadedFile("one.jpg", b"one", content_type="image/jpeg"),
            prediction="NORMAL",
            confidence=0.9,
            risk_level="LOW",
        )
        DoctorAssignment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            assigned_by=self.admin,
            scheduled_at=timezone.now() + timedelta(days=1),
        )

        response = self.client.get("/api/admin/reports/summary/?period=weekly")
        self.assertEqual(response.status_code, 200)
        self.assertIn("patient_growth", response.data)
        self.assertIn("scan_volume", response.data)
        self.assertIn("doctor_assignment_distribution", response.data)
        self.assertIn("disease_distribution", response.data)

        self.authenticate(self.doctor)
        denied = self.client.get("/api/admin/reports/summary/?period=weekly")
        self.assertEqual(denied.status_code, 403)

    @patch("diagnosis.views.build_medical_report_pdf")
    def test_doctor_generates_pdf_report_for_scan(self, mock_pdf):
        mock_pdf.return_value = ContentFile(b"%PDF-1.4\nfake\n")
        scan = ScanResult.objects.create(
            patient=self.patient,
            uploaded_by=self.doctor,
            original_image=SimpleUploadedFile("one.jpg", b"one", content_type="image/jpeg"),
            prediction="NORMAL",
            confidence=0.9,
            risk_level="LOW",
        )

        self.authenticate(self.doctor)
        response = self.client.post(f"/api/scans/{scan.id}/report/generate/")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["patient_id"], "P001")
        self.assertTrue(scan.medical_report.report_pdf.name.endswith(".pdf"))

    @patch("diagnosis.views.build_medical_report_pdf")
    def test_patient_can_preview_own_generated_report(self, mock_pdf):
        mock_pdf.return_value = ContentFile(b"%PDF-1.4\nfake\n")
        scan = ScanResult.objects.create(
            patient=self.patient,
            uploaded_by=self.doctor,
            original_image=SimpleUploadedFile("one.jpg", b"one", content_type="image/jpeg"),
            prediction="NORMAL",
            confidence=0.9,
            risk_level="LOW",
        )
        self.authenticate(self.doctor)
        generated = self.client.post(f"/api/scans/{scan.id}/report/generate/")

        self.authenticate(self.patient)
        response = self.client.get(f"/api/reports/{generated.data['id']}/preview/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")

    @patch("diagnosis.views.build_medical_report_pdf")
    def test_generating_doctor_is_saved_on_report(self, mock_pdf):
        second_doctor = User.objects.create_user(username="doctor2", password="Pass12345!", doctor_id="D002")
        set_user_group(second_doctor, DOCTOR_GROUP)
        mock_pdf.return_value = ContentFile(b"%PDF-1.4\nfake\n")
        scan = ScanResult.objects.create(
            patient=self.patient,
            uploaded_by=self.doctor,
            original_image=SimpleUploadedFile("one.jpg", b"one", content_type="image/jpeg"),
            prediction="NORMAL",
            confidence=0.9,
            risk_level="LOW",
        )

        self.authenticate(second_doctor)
        response = self.client.post(f"/api/scans/{scan.id}/report/generate/")

        self.assertEqual(response.status_code, 201)
        scan.refresh_from_db()
        self.assertEqual(scan.medical_report.doctor, second_doctor)

    @patch("diagnosis.views.build_medical_report_pdf")
    def test_admin_can_update_and_delete_report(self, mock_pdf):
        mock_pdf.return_value = ContentFile(b"%PDF-1.4\nfake\n")
        second_doctor = User.objects.create_user(username="doctor2", password="Pass12345!", doctor_id="D002")
        set_user_group(second_doctor, DOCTOR_GROUP)
        scan = ScanResult.objects.create(
            patient=self.patient,
            uploaded_by=self.doctor,
            original_image=SimpleUploadedFile("one.jpg", b"one", content_type="image/jpeg"),
            prediction="NORMAL",
            confidence=0.9,
            risk_level="LOW",
        )

        self.authenticate(self.doctor)
        generated = self.client.post(f"/api/scans/{scan.id}/report/generate/")

        self.authenticate(self.admin)
        updated = self.client.patch(
            f"/api/admin/reports/{generated.data['id']}/",
            {"doctor_id": "D002", "regenerate_pdf": True},
            format="json",
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.data["doctor_name"], "doctor2")

        deleted = self.client.delete(f"/api/admin/reports/{generated.data['id']}/")
        self.assertEqual(deleted.status_code, 204)

    @patch("diagnosis.views.build_medical_report_pdf")
    def test_doctor_cannot_edit_or_delete_report_via_admin_endpoint(self, mock_pdf):
        mock_pdf.return_value = ContentFile(b"%PDF-1.4\nfake\n")
        scan = ScanResult.objects.create(
            patient=self.patient,
            uploaded_by=self.doctor,
            original_image=SimpleUploadedFile("one.jpg", b"one", content_type="image/jpeg"),
            prediction="NORMAL",
            confidence=0.9,
            risk_level="LOW",
        )

        self.authenticate(self.doctor)
        generated = self.client.post(f"/api/scans/{scan.id}/report/generate/")

        denied_patch = self.client.patch(
            f"/api/admin/reports/{generated.data['id']}/",
            {"regenerate_pdf": True},
            format="json",
        )
        denied_delete = self.client.delete(f"/api/admin/reports/{generated.data['id']}/")

        self.assertEqual(denied_patch.status_code, 403)
        self.assertEqual(denied_delete.status_code, 403)

    @patch("diagnosis.views.build_medical_report_pdf")
    def test_patient_cannot_edit_or_delete_report_via_admin_endpoint(self, mock_pdf):
        mock_pdf.return_value = ContentFile(b"%PDF-1.4\nfake\n")
        scan = ScanResult.objects.create(
            patient=self.patient,
            uploaded_by=self.doctor,
            original_image=SimpleUploadedFile("one.jpg", b"one", content_type="image/jpeg"),
            prediction="NORMAL",
            confidence=0.9,
            risk_level="LOW",
        )

        self.authenticate(self.doctor)
        generated = self.client.post(f"/api/scans/{scan.id}/report/generate/")

        self.authenticate(self.patient)
        denied_patch = self.client.patch(
            f"/api/admin/reports/{generated.data['id']}/",
            {"regenerate_pdf": True},
            format="json",
        )
        denied_delete = self.client.delete(f"/api/admin/reports/{generated.data['id']}/")

        self.assertEqual(denied_patch.status_code, 403)
        self.assertEqual(denied_delete.status_code, 403)
