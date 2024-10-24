from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import FollowSerializer, LogoutUserSerializer, PasswordResetRequestSerializer, SetNewPasswordSerializer, UserRegisterSerializer, LoginSerializer, ProfileSerializer,PostSerializer,CommentSerializer
from .utilis import send_code_to_user
from .models import OneTimePassword, Post, User, Profile,Comment,Follow
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import smart_str, DjangoUnicodeDecodeError
from django.contrib.auth.tokens import PasswordResetTokenGenerator 
from django.shortcuts import get_object_or_404

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
    # Retrieve the existing profile
    profile = get_object_or_404(Profile, id=profile_id)

    # Initialize a dictionary to hold updates
    updated_data = {}

    # Check incoming data and prepare updates only if they differ
    bio = request.data.get('bio')
    if bio is not None and bio != profile.bio:
        updated_data['bio'] = bio

    profile_picture = request.data.get('profile_picture')
    if profile_picture is not None and profile_picture != profile.profile_picture:
        updated_data['profile_picture'] = profile_picture

    location = request.data.get('location')
    if location is not None and location != profile.location:
        updated_data['location'] = location

    # If no updates are necessary, return a 204 response
    if not updated_data:
        return Response({"message": "No changes detected."}, status=status.HTTP_204_NO_CONTENT)

    # Use the serializer to update the profile with the new data
    serializer = ProfileSerializer(profile, data=updated_data, partial=True)

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    # Handle validation errors
    print(serializer.errors)  # Log errors for debugging
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




@api_view(['POST'])
@permission_classes([IsAuthenticated])
def creating_post(request):
    # Ensure user is authenticated
    if request.user.is_anonymous:
        return Response({"error": "User is not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)
    
    # Creating an instance of Post and passing new data to it
    serializer = PostSerializer(data=request.data)

    if serializer.is_valid():
        validated_data = serializer.validated_data

        # Checking for existing posts with the same details
        existing_posts = Post.objects.filter(
            image=validated_data['image'],
            content=validated_data['content'],
        ).exists()

        # If a duplicate exists, throw an error
        if existing_posts:
            return Response({"error": "A Post with these details already exists"}, status=status.HTTP_400_BAD_REQUEST)

        # Saving the Post with the current authenticated user as the author
        serializer.save(author=request.user)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # If the data is not valid, return an error response
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(['GET'])
def list_posts(request,post_id=None):
    if post_id:
        #if post id provided , return specific profile
        post =get_object_or_404(Post, id=post_id)    
        serializer = PostSerializer(post)
    else:
        posts  = Post.objects.all().order_by('id')
        serializer = PostSerializer(posts, many=True)    

    return Response(serializer.data, status=status.HTTP_200_OK)  


@api_view(['PUT'])
def update_posts(request, post_id):
    # Find the post in the database using post_id
    try:
        post = Post.objects.get(id=post_id)  # Use the Post model to retrieve the post
    except Post.DoesNotExist:
        # If the post does not exist, return an error
        return Response({"error": "Post not found"}, status=status.HTTP_400_BAD_REQUEST)

    # Determine if the request is partial (for PATCH requests)
    partial = request.method == "PATCH"
    
    # Pass the existing post and new data to the serializer
    serializer = PostSerializer(post, data=request.data, partial=partial)
    
    # Check if the provided data is valid
    if serializer.is_valid():
        # Save the updated post to the database
        serializer.save()
        # Respond with updated post data and a success message
        return Response({"message": "Post updated successfully", "data": serializer.data}, status=status.HTTP_200_OK)
    
    # Return error details if the data is invalid
    return Response({"error": "Invalid data", "details": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    
@api_view(['DELETE'])
def delete_post(request, post_id):
    try:
        post = Post.objects.get(pk=post_id)
        post.delete()
        return Response({"message": "Post deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
    except Post.DoesNotExist:
        return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)




@api_view(['POST'])
@permission_classes([IsAuthenticated])
def post_comment(request, post_id):
    try:
        # Retrieve the post to which the comment is being added
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)

    # Add the logged-in user and the post to the request data
    data = request.data.copy()
    data['user'] = request.user.id  # Set the logged-in user
    data['post'] = post.id  # Set the post

    # Serialize the data
    serializer = CommentSerializer(data=data)
    if serializer.is_valid():
        # Save the comment to the database
        serializer.save()
        return Response({"message": "Comment posted successfully", "data": serializer.data}, status=status.HTTP_201_CREATED)
    
    return Response({"error": "Invalid data", "details": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)



@api_view(['GET'])
def list_comments(request,comment_id=None):
    if comment_id:
        #if comment id provided , return specific profile
        comment =get_object_or_404(Comment, id=comment_id)    
        serializer = CommentSerializer(comment)
    else:
        comments  = Comment.objects.all().order_by('id')
        serializer = CommentSerializer(comments, many=True)    

    return Response(serializer.data, status=status.HTTP_200_OK)  
    

@api_view(['DELETE'])
def  delete_comment(request,comment_id):

    try:
        comment = Comment.objects.get(pk=comment_id)
        comment.delete()
        return Response({"message","comment deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
    except Comment.DoesNotExist:
        return Response({"error","comment not found"}, status=status.HTTP_400_BAD_REQUEST)
    




@api_view(['POST'])
@permission_classes([IsAuthenticated])
def follow_user(request, user_id):
    try: 
        following_user = User.objects.get(id=user_id)
        
        if request.user == following_user:
            return Response({"detail": "You cannot follow yourself."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if the follow relationship already exists
        if Follow.objects.filter(follower=request.user, following=following_user).exists():
            return Response({"detail": "You are already following this user."}, status=status.HTTP_400_BAD_REQUEST)

        # Create the follow relationship
        Follow.objects.create(follower=request.user, following=following_user)
        return Response({"detail": f"You are now following {following_user.email}"}, status=status.HTTP_201_CREATED)
    
    except User.DoesNotExist:
        return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)
       

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def unfollow_user(request, user_id):
    try:
        following_user = User.objects.get(id=user_id)

        # Checking if the follow relationship exists
        follow_instance = Follow.objects.filter(follower=request.user, following=following_user).first()
        if not follow_instance:
            return Response({"detail": "You are not following this user."}, status=status.HTTP_400_BAD_REQUEST)
          
        # Delete the follow relationship
        follow_instance.delete()
        return Response({"detail": f"You have unfollowed {following_user.email}"}, status=status.HTTP_204_NO_CONTENT)
    
    except User.DoesNotExist:
        return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_followers(request):
    followers = Follow.objects.filter(following=request.user)
    serializer = FollowSerializer(followers, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_following(request):
    following = Follow.objects.filter(follower=request.user)
    serializer = FollowSerializer(following, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)
