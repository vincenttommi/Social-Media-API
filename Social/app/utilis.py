import random
from django.core.mail import EmailMessage
from django.core.mail import BadHeaderError
from Social import settings
from .models import User, OneTimePassword

def generate_otp():
    otp = "".join([str(random.randint(1, 9)) for _ in range(6)])  # Generate 6-digit OTP
    return otp



def send_code_to_user(email):
    subject = "One-time passcode for Email Verification"
    otp_code = generate_otp()
    print(f"Generated OTP: {otp_code}")  # Debugging: Print OTP to console

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return {"error": "User with this email does not exist."}

    current_site = "Social"
    email_body = (
        f"Hi {user.first_name},\n\n"
        f"Thanks for signing up on {current_site}. "
        f"Please verify your email with the following one-time passcode: {otp_code}."
    )

    # Save the OTP to the database
    OneTimePassword.objects.create(user=user, code=otp_code)

    # Send the email
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = [email]
    
    email_message = EmailMessage(
        subject=subject,
        body=email_body,
        from_email=from_email,
        to=to_email,
    )

    try:
        email_message.send(fail_silently=False)
        print(f"Email sent to {email}")
    except BadHeaderError as e:
        print(f"Failed to send email due to bad header: {e}")
        return {"error": "Invalid header found."}
    except Exception as e:
        print(f"Failed to send email: {e}")
        return {"error": "Failed to send email."}
    


def send_normal_email(data):
    email=EmailMessage(
        subject=data['email_subject'],
        body=data['email_body'],
       from_email=settings.EMAIL_HOST_USER,
        to=[data['to_email']]
    )
    email.send()




