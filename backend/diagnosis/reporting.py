from io import BytesIO
from pathlib import Path

from django.conf import settings
from PIL import Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


def _draw_text(c, text, x, y, size=10, bold=False, color=colors.HexColor("#111827")):
    c.setFillColor(color)
    c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
    c.drawString(x, y, text or "")


def _draw_center(c, text, x, y, size=10, bold=False, color=colors.HexColor("#111827")):
    c.setFillColor(color)
    c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
    c.drawCentredString(x, y, text or "")


def _image_reader(path, remove_dark_background=False):
    if not path or not Path(path).exists():
        return None
    if not remove_dark_background:
        return ImageReader(str(path))

    image = Image.open(path).convert("RGBA")
    pixels = image.load()
    width, height = image.size
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            if a and r < 38 and g < 38 and b < 38:
                pixels[x, y] = (255, 255, 255, 0)
    return ImageReader(image)


def _draw_file_image(c, file_field, x, y, width, height):
    if not file_field:
        return False
    reader = _image_reader(getattr(file_field, "path", ""))
    if not reader:
        return False
    c.drawImage(reader, x, y, width=width, height=height, preserveAspectRatio=True, anchor="c", mask="auto")
    return True


def _field_line(c, label, value, x, y, width):
    _draw_text(c, label, x, y + 14, 9, False, colors.HexColor("#374151"))
    _draw_text(c, value, x, y + 3, 9, False, colors.HexColor("#111827"))
    c.setStrokeColor(colors.HexColor("#b8c1cc"))
    c.line(x, y, x + width, y)


def _section(c, title, x, y, width):
    c.setFillColor(colors.HexColor("#f1f3f6"))
    c.rect(x, y, width, 22, fill=True, stroke=False)
    _draw_text(c, title, x + 10, y + 7, 11, True)


def _wrapped_lines(text, max_chars=92):
    words = (text or "").split()
    lines = []
    current = []
    for word in words:
        candidate = " ".join(current + [word])
        if len(candidate) > max_chars and current:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    return lines or [""]


def build_medical_report_pdf(scan, doctor=None):
    patient = scan.patient
    doctor = doctor or scan.uploaded_by
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    margin = 58
    content_width = width - (2 * margin)
    blue = colors.HexColor("#2563eb")
    title_blue = colors.HexColor("#064e80")

    logo_path = Path(settings.PROJECT_ROOT) / "frontend" / "MedicalDiagnosisGUI" / "icons" / "logo.png"
    logo_reader = _image_reader(logo_path, remove_dark_background=True)
    if logo_reader:
        c.drawImage(
            logo_reader,
            (width - 188) / 2,
            704,
            width=188,
            height=102,
            preserveAspectRatio=True,
            anchor="c",
            mask="auto",
        )
    else:
        _draw_center(c, "MEDICARE", width / 2, 742, 24, True, title_blue)

    _draw_center(c, "MEDICARE DIAGNOSIS CENTER", width / 2, 688, 10, True, title_blue)
    _draw_center(c, "Address: Yangzhou, China", width / 2, 662, 10)
    _draw_center(c, "Phone: 1234567891", width / 2, 642, 10)
    _draw_center(c, "Email: admin@admin.com", width / 2, 622, 10)
    c.setStrokeColor(blue)
    c.setLineWidth(1.1)
    c.line(margin, 598, width - margin, 598)

    report_date = scan.created_at.strftime("%m/%d/%Y")
    _draw_center(c, "MEDICAL REPORT", width / 2, 570, 17, True)
    _draw_center(c, f"Date: {report_date}", width / 2, 547, 10)

    _section(c, "Patient Information", margin, 506, content_width)
    patient_name = patient.get_full_name() or patient.username
    age_gender = " / ".join(part for part in [str(patient.age or ""), patient.gender] if part)
    _field_line(c, "Patient Name:", patient_name, margin + 10, 468, 190)
    _field_line(c, "Patient ID:", patient.patient_id or "", margin + 265, 468, 185)
    _field_line(c, "Age/Gender:", age_gender, margin + 10, 426, 190)
    _field_line(c, "Contact Number:", patient.phone_number or "", margin + 265, 426, 185)

    _section(c, "Diagnosis Results", margin, 380, content_width)
    _draw_text(c, "Diagnosis:", margin + 10, 354, 10)
    c.setStrokeColor(colors.HexColor("#cbd5e1"))
    c.rect(margin + 10, 306, content_width - 20, 38, fill=False, stroke=True)
    diagnosis = f"{scan.prediction} | Confidence: {scan.confidence * 100:.1f}% | Risk: {scan.risk_level}"
    line_y = 328
    for line in _wrapped_lines(diagnosis):
        _draw_text(c, line, margin + 18, line_y, 10)
        line_y -= 13

    _draw_text(c, "Grad-CAM Heatmap Analysis:", margin + 10, 282, 10)
    heatmap_x = margin + 10
    heatmap_y = 178
    heatmap_w = content_width - 20
    heatmap_h = 88
    c.setDash(2, 2)
    c.setStrokeColor(colors.HexColor("#cbd5e1"))
    c.rect(heatmap_x, heatmap_y, heatmap_w, heatmap_h, fill=False, stroke=True)
    c.setDash()
    if not _draw_file_image(c, scan.heatmap_image, heatmap_x + 5, heatmap_y + 5, heatmap_w - 10, heatmap_h - 10):
        _draw_center(c, "Grad-CAM heatmap image will be generated here", width / 2, heatmap_y + 42, 9, False, colors.HexColor("#94a3b8"))

    _section(c, "Doctor Information", margin, 136, content_width)
    doctor_name = (doctor.get_full_name() or doctor.username) if doctor else ""
    doctor_id = getattr(doctor, "doctor_id", "") if doctor else ""
    specialty = getattr(doctor, "specialization", "") if doctor else ""
    _field_line(c, "Examined By:", doctor_name, margin + 10, 103, 150)
    _field_line(c, "Doctor ID:", doctor_id, margin + 190, 103, 120)
    _field_line(c, "Specialization:", specialty, margin + 330, 103, 150)
    _field_line(c, "Date:", report_date, margin + 10, 66, 150)

    sig_y = 68
    if doctor:
        _draw_file_image(c, doctor.electronic_signature, margin + 230, sig_y + 8, 180, 38)
    c.setStrokeColor(colors.HexColor("#6b7280"))
    c.line(margin + 10, sig_y, margin + 160, sig_y)
    c.line(margin + 230, sig_y, margin + 430, sig_y)
    _draw_text(c, "Date", margin + 10, sig_y - 14, 8)
    _draw_text(c, "Doctor's Signature", margin + 230, sig_y - 14, 8)

    c.setStrokeColor(colors.HexColor("#cbd5e1"))
    c.line(margin, 35, width - margin, 35)
    _draw_center(c, "This is an official medical report from Medicare Diagnosis Center", width / 2, 22, 8, False, colors.HexColor("#475569"))
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer
