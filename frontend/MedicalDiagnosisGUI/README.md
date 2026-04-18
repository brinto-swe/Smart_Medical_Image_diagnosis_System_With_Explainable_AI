# MediCare JavaFX Frontend

JavaFX desktop UI for the SmartMedicalProject DRF backend.

## Requirements

- JDK: `C:\Program Files\Java\jdk-26`
- JavaFX jars: `lib/*.jar`
- JavaFX native DLLs: `C:\Users\mozad\Downloads\openjfx-26_windows-x64_bin-sdk\javafx\bin`
- Backend running at `http://127.0.0.1:8000`

## Run From VS Code

Open this folder in VS Code and run **Launch Java Program**. The launch config uses:

```text
C:\Program Files\Java\jdk-26\bin\java.exe
```

## Compile Manually

```powershell
& 'C:\Program Files\Java\jdk-26\bin\javac.exe' --module-path '.\lib' --add-modules javafx.controls,javafx.fxml -d '.\bin' '.\src\*.java'
```

## Run Manually

```powershell
$env:PATH = 'C:\Users\mozad\Downloads\openjfx-26_windows-x64_bin-sdk\javafx\bin;' + $env:PATH
& 'C:\Program Files\Java\jdk-26\bin\java.exe' --module-path '.\lib' --add-modules javafx.controls,javafx.fxml --enable-native-access=javafx.graphics -cp '.\bin' App
```

## Implemented Screens

- Role-style login and patient signup
- Admin dashboard, doctor management, patient management, reports summary
- Doctor dashboard, patient search, X-ray upload, scan history
- Doctor profile editing, profile picture upload, electronic signature upload, and change password
- Patient dashboard, own reports, report preview/download, editable profile, profile picture upload, change password
- Admin report search with preview/download actions
- SMTP password reset request trigger

## Backend API Used

- `POST /api/auth/signup/`
- `POST /api/auth/login/`
- `POST /api/auth/logout/`
- `POST /api/auth/password-reset/`
- `GET/PATCH /api/profile/`
- `POST /api/profile/change-password/`
- `GET/POST /api/admin/doctors/`
- `GET/POST /api/admin/patients/`
- `GET /api/admin/reports/summary/`
- `GET /api/doctor/patients/search/`
- `POST /api/doctor/xray/upload/`
- `GET /api/scans/`
- `POST /api/scans/<scan_id>/report/generate/`
- `GET /api/reports/`
- `GET /api/reports/<report_id>/preview/`
- `GET /api/reports/<report_id>/download/`
