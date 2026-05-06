# SMTP (Simple Mail Transfer Protocol)

SMTP is the internet standard protocol for sending emails. The system uses Python's built-in `smtplib` to connect to Gmail's SMTP server (`smtp.gmail.com:465` over SSL) and dispatch automated violation notices.

## Flow
1. Credentials (`SMTP_EMAIL`, `SMTP_APP_PASSWORD`) are loaded from the `.env` file using `python-dotenv`.
2. An `EmailMessage` object is constructed with the violation notice body (Rs. 500 fine).
3. The full annotated violation frame is attached as a JPEG.
4. The email is sent via an SSL-encrypted connection to the violator's email address retrieved from SQLite.
