import smtplib
from email.message import EmailMessage
import mimetypes
import os
import config

def send_violation_email(to_email: str, name: str, violation_image_path: str) -> bool:
    """
    Send an email notification about the littering violation with the attached image.
    """
    sender_email = config.SMTP_EMAIL
    app_password = config.SMTP_APP_PASSWORD

    if not sender_email or not app_password:
        print("[Emailer] SMTP credentials not configured. Skipping email.")
        return False

    msg = EmailMessage()
    msg['Subject'] = 'Notice: Littering Violation Detected'
    msg['From'] = sender_email
    msg['To'] = to_email

    body = f"""Dear {name},

This is an automated notice from the SwachhBharat Littering Detection System.

You have been recorded violating the public cleanliness rules by throwing garbage in an unauthorized area. As per the municipal guidelines, you are charged with a fine of Rs. 500.

Please find the photographic evidence attached to this email.

We urge you to maintain cleanliness and use designated dustbins in the future.

Regards,
Project Drishti - SwachhBharat Administration
"""
    msg.set_content(body)

    # Attach the violation image
    if os.path.exists(violation_image_path):
        ctype, encoding = mimetypes.guess_type(violation_image_path)
        if ctype is None or encoding is not None:
            ctype = 'application/octet-stream'
        maintype, subtype = ctype.split('/', 1)

        with open(violation_image_path, 'rb') as f:
            image_data = f.read()

        msg.add_attachment(image_data, maintype=maintype, subtype=subtype, filename=os.path.basename(violation_image_path))
    else:
        print(f"[Emailer] Warning: Violation image not found at {violation_image_path}")

    try:
        # Connect to Gmail SMTP server
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender_email, app_password)
            smtp.send_message(msg)
        print(f"[Emailer] Violation email successfully sent to {to_email}")
        return True
    except Exception as e:
        print(f"[Emailer] Failed to send email to {to_email}. Error: {e}")
        return False
