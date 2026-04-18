from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from accounts.views import (
    ChangePasswordView,
    DoctorDetailView,
    DoctorListCreateView,
    LoginView,
    LogoutView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    PatientDetailView,
    PatientListCreateView,
    ProfileView,
    RoleChangeView,
    SignupView,
)
from diagnosis.views import (
    AdminReportSummaryView,
    DoctorPatientSearchView,
    PatientHistoryView,
    PredictXrayView,
    RecentScanListView,
    ReportView,
    ScanDetailView,
    ScanListView,
)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/signup/", SignupView.as_view(), name="signup"),
    path("api/auth/login/", LoginView.as_view(), name="login"),
    path("api/auth/logout/", LogoutView.as_view(), name="logout"),
    path("api/auth/password-reset/", PasswordResetRequestView.as_view(), name="password-reset"),
    path("api/auth/password-reset/confirm/", PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
    path("api/profile/", ProfileView.as_view(), name="profile"),
    path("api/profile/change-password/", ChangePasswordView.as_view(), name="change-password"),
    path("api/admin/doctors/", DoctorListCreateView.as_view(), name="admin-doctors"),
    path("api/admin/doctors/<int:pk>/", DoctorDetailView.as_view(), name="admin-doctor-detail"),
    path("api/admin/patients/", PatientListCreateView.as_view(), name="admin-patients"),
    path("api/admin/patients/<int:pk>/", PatientDetailView.as_view(), name="admin-patient-detail"),
    path("api/admin/users/<int:user_id>/role/", RoleChangeView.as_view(), name="admin-role-change"),
    path("api/admin/reports/summary/", AdminReportSummaryView.as_view(), name="admin-report-summary"),
    path("api/doctor/patients/search/", DoctorPatientSearchView.as_view(), name="doctor-patient-search"),
    path("api/doctor/xray/upload/", PredictXrayView.as_view(), name="doctor-xray-upload"),
    path("api/scans/", ScanListView.as_view(), name="scan-list"),
    path("api/scans/recent/", RecentScanListView.as_view(), name="recent-scans"),
    path("api/scans/<int:pk>/", ScanDetailView.as_view(), name="scan-detail"),
    path("api/patients/<str:patient_id>/history/", PatientHistoryView.as_view(), name="patient-history"),
    path("api/reports/<int:scan_id>/", ReportView.as_view(), name="scan-report"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
