from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import LogoutUserSerializer, PasswordResetRequestSerializer, SetNewPasswordSerializer, UserRegisterSerializer, LoginSerializer, ProfileSerializer
from .utilis import send_code_to_user
from .models import OneTimePassword, User, Profile
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import smart_str, DjangoUnicodeDecodeError
from django.contrib.auth.tokens import PasswordResetTokenGenerator 

@api_view(['POST'])
def user_register(request):
    serializer = UserRegisterSerializer(data=request.data)

    if serializer.is_valid(raise_exception=True):
        serializer.save()
        user = serializer.data

        try:
            send_code_to_user(user['email'])
        except Exception as e:
            print(f"Failed to send email: {e}")
            return Response({"error": "Email sending failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            'data': user,
            'message': f'Hi {user["first_name"]}, thanks for signing up! A passcode has been sent to your email.'
        })

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def login_user(request):
    serializer = LoginSerializer(data=request.data)
    
    if serializer.is_valid():
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def verify_user_email(request):
    otp_code = request.data.get('otp')
    if not otp_code:
        return Response({"message": "Passcode not provided"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user_code_obj = OneTimePassword.objects.get(code=otp_code)
        user = user_code_obj.user
        if not user.is_verified:
            user.is_verified = True
            user.save()
            return Response({"message": "Account verified successfully"}, status=status.HTTP_200_OK)
        return Response({"message": "User already verified"}, status=status.HTTP_200_OK)
    except OneTimePassword.DoesNotExist:
        return Response({"message": "Invalid passcode"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"Error during verification: {e}")
        return Response({"message": "Something went wrong"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def set_new_password(request):
    serializer = SetNewPasswordSerializer(data=request.data)
    if serializer.is_valid(raise_exception=True):
        serializer.save()
        return Response({"message": "Password reset successful"}, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def password_reset_request(request):
    serializer = PasswordResetRequestSerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    return Response({'message': 'A link has been sent to your email to reset your password.'}, status=status.HTTP_200_OK)


@api_view(['POST'])
def password_reset_confirm(request, uidb64, token):
    try:
        user_id = smart_str(urlsafe_base64_decode(uidb64))
        user = get_object_or_404(User, id=user_id)

        if not PasswordResetTokenGenerator().check_token(user, token):
            return Response({'success': False, 'message': 'Token is invalid or has expired'}, status=status.HTTP_401_UNAUTHORIZED)

        return Response({'success': True, 'message': 'Credentials are valid', 'uidb64': uidb64, 'token': token}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'success': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_user(request):
    serializer = LogoutUserSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    
    return Response({"message": "Logout successfully"}, status=status.HTTP_200_OK)


@api_view(['POST'])
def create_profile(request):
    email = request.data.get('email')
    
    if not email:
        return Response({"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)
    
    user = get_object_or_404(User, email=email)

    if Profile.objects.filter(user=user).exists():
        return Response({"error": "A profile for this user already exists."}, status=status.HTTP_400_BAD_REQUEST)

    serializer = ProfileSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(user=user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def view_profile(request,profile_id=None):
    if profile_id:
        #if profile id provided , return specific profile
        profile =get_object_or_404(Profile, id=profile_id)    
        serializer = ProfileSerializer(profile)
    else:
        profiles  = Profile.objects.all().order_by('id')
        serializer = ProfileSerializer(profiles, many=True)    

    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['PUT'])
def update_profile(request, profile_id):
    # Retrieve the existing profile or return a 404 if not found
    profile = get_object_or_404(Profile, id=profile_id)

    # Compare existing profile data with incoming request data
    incoming_data = {
        'bio': request.data.get('bio', profile.bio),
        'profile_picture': request.data.get('profile_picture', profile.profile_picture),
        'location': request.data.get('location', profile.location)
    }

    # Check if any fields have changed; if not, return a 204 response
    if (incoming_data['bio'] == profile.bio and
        incoming_data['profile_picture'] == profile.profile_picture and
        incoming_data['location'] == profile.location):
        return Response({"message": "No changes detected."}, status=status.HTTP_204_NO_CONTENT)

    # If changes are detected, update the profile using the serializer
    serializer = ProfileSerializer(profile, data=incoming_data)

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    # Handle validation errors
    print(serializer.errors)  # Log errors for debugging
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
