from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile
from allauth.account.signals import user_signed_up

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()
        
@receiver(user_signed_up)
def populate_profile_from_google(sender, user, **kwargs):
    from allauth.socialaccount.models import SocialAccount
    try:
        social = user.socialaccount_set.get(provider='google')
        data = social.extra_data
        profile = user.profile
        profile.full_name = data.get('name', '')
        profile.email = data.get('email', '')
        # Optional: download avatar
        import urllib.request
        from django.core.files import File
        from django.core.files.temp import NamedTemporaryFile

        picture_url = data.get('picture')
        if picture_url:
            img_temp = NamedTemporaryFile(delete=True)
            img_temp.write(urllib.request.urlopen(picture_url).read())
            img_temp.flush()
            profile.avatar.save(f"avatar_{user.id}.jpg", File(img_temp))
        profile.save()
    except:
        pass