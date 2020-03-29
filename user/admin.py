from django.contrib import admin
from user.models import UserInfo, Token


admin.site.register(UserInfo)
admin.site.register(Token)
