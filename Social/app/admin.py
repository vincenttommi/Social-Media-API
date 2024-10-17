from django.contrib import admin

# Register your models here.
from .models import User,Profile,Comment,OneTimePassword,Post,Notification



admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(OneTimePassword)
admin.site.register(Notification)
admin.site.register(User)






