from django.contrib import admin
from pokerboard.models import PokerBoard, Role, Issue, UserEstimate, Group , InviteEmail, Player , UserCard , AcceptRequest
admin.site.register(PokerBoard)
admin.site.register(Role)
admin.site.register(Issue)
admin.site.register(UserEstimate)
admin.site.register(Group)
admin.site.register(InviteEmail)
admin.site.register(AcceptRequest)
admin.site.register(Player)
admin.site.register(UserCard)
