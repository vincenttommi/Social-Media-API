from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from .managers import UserManager
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import AuthenticationFailed


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)  # Make sure this exists
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']


    def __str__(self):
        return f"{self.first_name}{self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def tokens(self):
        try:
            refresh = RefreshToken.for_user(self)
            return {
                'refresh': str(refresh),
                'access': str(refresh.access_token)
            }
        except Exception as e:
            raise AuthenticationFailed('Error generating tokens')



class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile of {self.user.email}"

        





class Post(models.Model):
    CATEGORY_CHOICES = [
        ('news', 'News'),
        ('sports', 'Sports'),
        ('politics', 'Politics'),
        ('lifestyle', 'Lifestyle'),
        ('fashion', 'Fashion'),
        ('business', 'Business'),
        ('tours_travel', 'Tours and Travel'),
        ('climate', 'Climate'),
        ('science', 'Science'),
        ('health', 'Health'),
        ('world', 'World'),
        ('technology', 'Technology'),
        ('matatu_culture', 'Matatu_calture'),

        

    ]

    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    image = models.ImageField(upload_to='post_images/', blank=True, null=True)
    title = models.CharField(max_length=255) 
    content = models.TextField()
    categories = models.CharField(max_length=50, choices=CATEGORY_CHOICES) 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.author.full_name()} - {self.content[:20]}"


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user.full_name} on {self.post}"


class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, blank=True, null=True)
    notification_type = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification for {self.recipient.full_name}"


class OneTimePassword(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6, unique=True)
    created_at = models.CharField(max_length=6)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.first_name} - passcode"


    