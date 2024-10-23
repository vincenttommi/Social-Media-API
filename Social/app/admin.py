from django.contrib import admin
from .models import User, Profile, Post, Comment,OneTimePassword

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_active', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name')

admin.site.register(Profile)
admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(OneTimePassword)
