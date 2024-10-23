from django.utils.encoding import smart_str, smart_bytes, force_str
from django.urls import reverse
from .models import User,Profile,Post,Comment,Follow
from .utilis import send_normal_email
from django.contrib.sites.shortcuts import get_current_site
from rest_framework_simplejwt.tokens import RefreshToken,TokenError
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import authenticate
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode,urlsafe_base64_decode 
from django.contrib.auth import get_user_model





class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(max_length=70, min_length=6, write_only=True)
    password2 = serializers.CharField(max_length=70, min_length=6, write_only=True)

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'password', 'password2']
        

    def validate(self, attrs):
        password = attrs.get('password', '')
        password2 = attrs.get('password2', '')

        if password != password2:
            raise serializers.ValidationError("Passwords do not match.")
        
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')  # We don't need to store this field
        user = User.objects.create_user(
            email=validated_data['email'],
            first_name=validated_data.get('first_name'),
            last_name=validated_data.get('last_name'),
            password=validated_data.get('password'),
            
        )
        return user




class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255, min_length=6)
    password = serializers.CharField(max_length=68, write_only=True)
    full_name = serializers.CharField(max_length=255, read_only=True)
    access_token = serializers.CharField(max_length=255, read_only=True)
    refresh_token = serializers.CharField(max_length=255, read_only=True)

    class Meta:
        fields = ['email', 'password', 'full_name', 'access_token', 'refresh_token']

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        # User retrieval
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise AuthenticationFailed('Invalid credentials, try again')

        # Password check
        if not user.check_password(password):
            raise AuthenticationFailed('Invalid credentials, try again')

        # Check if user is verified
        if not user.is_verified:
            raise AuthenticationFailed('Your email is not verified. Please verify your email before logging in.')

        # Token generation
        user_token = user.tokens()  # Ensure this is returning a dictionary, not a string

        # Add user details to validated attrs
        attrs['full_name'] = user.full_name  
        attrs['access_token'] = str(user_token.get('access'))
        attrs['refresh_token'] = str(user_token.get('refresh'))
        attrs['user'] = user 

        return attrs



class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)

    def validate(self, attrs):
        email = attrs.get('email')
        if User.objects.filter(email=email).exists():  # Use exists() for checking
            user = User.objects.get(email=email)
            uidb64 = urlsafe_base64_encode(smart_bytes(user.id))
            token = PasswordResetTokenGenerator().make_token(user)

            # Accessing the request context properly
            request = self.context.get('request')
            site_domain = get_current_site(request).domain
            relative_link = reverse('password-reset-confirm', kwargs={'uidb64': uidb64, 'token': token})
            abslink = f"http://{site_domain}{relative_link}"
            email_body = f"Hi, use the link below to reset your password:\n{abslink}"

            data = {
                'email_body': email_body,
                'email_subject': "Reset your password",
                'to_email': user.email
            }
            send_normal_email(data)
        else:
            raise serializers.ValidationError("User with this email does not exist.")
        
        return attrs


class SetNewPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(max_length=100, min_length=6, write_only=True)
    confirm_password = serializers.CharField(max_length=100, min_length=6, write_only=True)
    uidb64 = serializers.CharField(write_only=True)
    token = serializers.CharField(write_only=True)

    def validate(self, attrs):
        token = attrs.get('token')
        uidb64 = attrs.get('uidb64')
        password = attrs.get('password')
        confirm_password = attrs.get('confirm_password')

        # Check if the passwords match
        if password != confirm_password:
            raise serializers.ValidationError("Passwords do not match.")

        # Decode the uidb64
        user_id = force_str(urlsafe_base64_decode(uidb64))
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise AuthenticationFailed("User not found.")

        # Validate the token
        if not PasswordResetTokenGenerator().check_token(user, token):
            raise AuthenticationFailed('Reset link is invalid or expired.')

        # If everything is fine, return the user object
        attrs['user'] = user
        return attrs

    def create(self, validated_data):
        user = validated_data['user']
        user.set_password(validated_data['password'])
        user.save()
        return user



class LogoutUserSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()
    default_error_messages ={
        'bad_token':('Token is Invalid or has expired')
    }

    def validate(self, attrs):
          self.token=attrs.get('refresh_token ')
          return (attrs)
    def save(self, **kwargs):
        try:
            token = RefreshToken(self.token)
            token.blacklist()
        except TokenError: 
            return self.fail('bad_token')     

User = get_user_model()

class ProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Profile
        fields = ['id','email', 'bio', 'profile_picture', 'location', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def validate(self, data):
        
        #check when creating a new profile(i.e no user assigned yet)
        if 'user' not in self.context:
            email = self.initial_data.get('email')
            if email:
                try:
                    user  = User.objects.get(email=email)
                except User.DoesNotExist:
                    raise serializers.ValidationError("No user is associated  with this email")
                self.context['user'] = user  #Store the user in the context
        return data 

    def create(self, validated_data):
        # Remove email from validated data as it's not a field in Profile model
        email = validated_data.pop('email', None)
        
        # Get the user from the context
        user = self.context['user']
        
        # Ensure 'user' is not in validated_data to avoid passing it twice
        validated_data.pop('user', None)

        # Create the profile using the user and the rest of the validated data
        profile = Profile.objects.create(user=user, **validated_data)
        return profile

    def update(self, instance, validated_data):
        # Update the profile details, similar to how you're already doing it
        instance.bio = validated_data.get('bio', instance.bio)
        instance.profile_picture = validated_data.get('profile_picture', instance.profile_picture)
        instance.location = validated_data.get('location', instance.location)
        instance.save()

        return instance



class PostSerializer(serializers.ModelSerializer):
    author = serializers.PrimaryKeyRelatedField(read_only=True)
    

    class Meta:
        model = Post
        fields = ['id', 'author', 'content', 'image', 'categories', 'created_at', 'updated_at']

    def create(self, validated_data):
        return Post.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.content = validated_data.get('content', instance.content)
        instance.image = validated_data.get('image', instance.image)
        instance.categories = validated_data.get('categories', instance.categories)
        instance.save()
        return instance


class CommentSerializer(serializers.ModelSerializer):
    user  = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    post = serializers.PrimaryKeyRelatedField(queryset=Post.objects.all())

    class Meta:
        model = Comment
        fields  = ['id','user','post','comments','created_at']
        read_only_fields = ['id','created_at']


class FollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields  = ['follower','following','followed_at']
        read_only_fields = ['follower','followed_at']



