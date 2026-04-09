from django.contrib import admin
from .models import Patient, ScanResult

admin.site.register(Patient)
admin.site.register(ScanResult)