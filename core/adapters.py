from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    """Custom adapter to automatically create/link users from social accounts.

    Behavior:
    - If a local user with the same email exists, link the social account to that user.
    - For brand-new social accounts, set a username derived from the email local-part
      and ensure the email is set, then save the user. This helps avoid the
      intermediate signup form and allows direct redirect to LOGIN_REDIRECT_URL.
    """

    def pre_social_login(self, request, sociallogin):
        # If social account is already linked to a user, do nothing
        if sociallogin.is_existing:
            return

        email = None
        # Try to get an email from social account data
        try:
            email = sociallogin.account.extra_data.get('email')
        except Exception:
            pass

        if not email:
            return

        User = get_user_model()
        try:
            user = User.objects.get(email__iexact=email)
            # Link this social account to the existing user and skip the signup form
            sociallogin.connect(request, user)
        except User.DoesNotExist:
            # No matching local user — allow the normal auto-signup flow to continue.
            return

    def save_user(self, request, sociallogin, form=None):
        """Save a new user (called during social signup).

        We ensure username and email are present. Username is derived from the
        email if not provided. Password is left unusable because auth is via
        the provider.
        """
        user = sociallogin.user

        # Ensure email is set from provider data when available
        email = user.email or sociallogin.account.extra_data.get('email')
        if email:
            user.email = email

        # Ensure username exists; derive from email local-part if needed
        if not user.username:
            if email:
                base = email.split('@', 1)[0]
                # Basic username; let DB constraints raise if collision occurs
                user.username = base
            else:
                # Fallback username
                user.username = sociallogin.account.uid

        # Do not set a usable password for social-only accounts
        user.set_unusable_password()
        user.save()

        # Complete the sociallogin save (creates SocialAccount, SocialToken, etc.)
        sociallogin.save(request)
        return user

    def is_open_for_signup(self, request, sociallogin):
        # Allow signups from social accounts (useful in dev/testing).
        return True
