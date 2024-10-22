from django.urls import path
from . import views 
urlpatterns = [
    path('register/', views.user_register, name='user-register'),  # User registration
    path('login/', views.login_user, name='login-user'),          # User login
    path('verify-email/', views.verify_user_email, name='verify-email'),  # Email verification
    path('set-new-password/', views.set_new_password, name='set-new-password'),  # Set new password
    path('password-reset-request/', views.password_reset_request, name='password-reset-request'),  # Password reset request
    path('password-reset-confirm/<str:uidb64>/<str:token>/', views.password_reset_confirm, name='password-reset-confirm'),  # Password reset confirmation
    path('logout/', views.logout_user, name='logout-user'),        # User logout
    path('create-profile/', views.create_profile, name='create-profile'),  # Create user profile
    path('view-profile/', views.view_profile, name='view-profile'),  # View all profiles
    path('update-profile/<int:profile_id>/',views.update_profile, name='update-profile'),  # Update a specific profile
    path('view-profile/<int:profile_id>/', views.view_profile, name='view-profile'),
    path('creating_post/', views.creating_post,name='creating_post'),
    path('list_posts/', views.list_posts,name='list_posts'),
    path('list_posts/<int:post_id>/', views.list_posts, name='list_posts'),


]
