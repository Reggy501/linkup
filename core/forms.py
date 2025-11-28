from django import forms
from allauth.account.forms import SignupForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError


class CustomSignupForm(SignupForm):
    """Signup form that prevents registering with an email already in use.

    This will add a validation error to the email field during local signup
    if another user already has that email (case-insensitive match).
    """

    def clean_email(self):
        email = self.cleaned_data.get('email')
        User = get_user_model()
        if email and User.objects.filter(email__iexact=email).exists():
            raise ValidationError("A user is already registered with this email address.")
        return email
