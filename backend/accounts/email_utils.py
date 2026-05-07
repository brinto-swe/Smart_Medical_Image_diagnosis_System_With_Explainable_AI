from email.mime.image import MIMEImage
from pathlib import Path

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


BRAND_NAME = "Medical Diagnosis Center"
LOGO_CID = "medical-diagnosis-center-logo"


def activation_link(request, user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    return request.build_absolute_uri(
        reverse("activate-account-link", kwargs={"uid": uid, "token": token})
    )


def password_reset_link(request, user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    reset_url = getattr(settings, "FRONTEND_PASSWORD_RESET_URL", "")
    if reset_url:
        return f"{reset_url}?uid={uid}&token={token}"
    api_path = reverse("password-reset-confirm")
    return f"{request.build_absolute_uri(api_path)}?uid={uid}&token={token}"


def send_activation_email(request, user):
    link = activation_link(request, user)
    name = user.get_full_name() or user.username
    return send_branded_email(
        subject="Confirm your Medical Diagnosis Center email",
        template_name="email/account_activation.html",
        recipient=user.email,
        context={
            "patient_name": name,
            "button_url": link,
            "button_text": "Confirm Email",
            "heading": "Confirm your email",
            "icon": "MDC",
            "preheader": "Confirm your email and get an appointment for diagnosis.",
        },
        text_body=(
            f"Hello {name}!\n\n"
            "Please confirm your email and get an appointment for diagnosis.\n"
            "We are wishing you best from Medical Diagnosis Center.\n\n"
            f"Confirm your email: {link}\n"
        ),
    )


def send_password_reset_email(request, user):
    link = password_reset_link(request, user)
    name = user.get_full_name() or user.username
    return send_branded_email(
        subject="Reset your Medical Diagnosis Center password",
        template_name="email/password_reset.html",
        recipient=user.email,
        context={
            "patient_name": name,
            "button_url": link,
            "button_text": "Reset Password",
            "heading": "Reset your password",
            "icon": "MDC",
            "preheader": "Reset your password securely.",
        },
        text_body=(
            f"Hello {name}!\n\n"
            "Did you forgot your password? Oh no... Don't worry, reset your password by clicking the link below.\n\n"
            f"Reset your password: {link}\n"
        ),
    )


def send_branded_email(subject, template_name, recipient, context, text_body):
    context = {
        **context,
        "brand_name": BRAND_NAME,
        "logo_cid": LOGO_CID,
        "support_email": getattr(settings, "DEFAULT_FROM_EMAIL", ""),
    }
    html_body = render_to_string(template_name, context)
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[recipient],
    )
    email.attach_alternative(html_body, "text/html")
    attach_inline_logo(email)
    email.send(fail_silently=False)


def attach_inline_logo(email):
    logo_path = Path(getattr(settings, "EMAIL_LOGO_PATH", ""))
    if not logo_path.exists():
        return
    with logo_path.open("rb") as file:
        logo = MIMEImage(file.read())
    logo.add_header("Content-ID", f"<{LOGO_CID}>")
    logo.add_header("Content-Disposition", "inline", filename=logo_path.name)
    email.attach(logo)
