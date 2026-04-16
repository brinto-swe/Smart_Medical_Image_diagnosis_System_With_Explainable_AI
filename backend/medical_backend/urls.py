from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.authtoken.views import obtain_auth_token
from accounts.views import login_view, create_doctor, get_doctors, delete_doctor, update_doctor

from diagnosis.views import (
    predict_view, create_patient, patient_history,
    search_patient, generate_report, scan_detail,
    recent_scans, all_scans
)

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/create-patient/', create_patient),
    path('api/predict/', predict_view),

    path('api/scans/', all_scans),
    path('api/scans/recent/', recent_scans),

    path('api/history/<int:patient_id>/', patient_history),
    path('api/search-patient/', search_patient),

    path('api/report/<int:scan_id>/', generate_report),
    path('api/scan/<int:scan_id>/', scan_detail),

    path('api/token/', obtain_auth_token),  # 🔥 THIS LINE MISSING ছিল

    path('api/login/', login_view),
    path('api/create-doctor/', create_doctor),
    path('api/doctors/', get_doctors),
    path('api/doctors/<int:doctor_id>/', delete_doctor),
    path('api/doctors/update/<int:doctor_id>/', update_doctor),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)