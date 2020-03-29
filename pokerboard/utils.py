from pokerboard.models import PokerBoard, Role
from user.models import UserInfo


def get_current_role(pokerboard_id, user_id):
        if(len(PokerBoard.objects.filter(id=pokerboard_id,group_spectator__user__id=user_id))+len(PokerBoard.objects.filter(id=pokerboard_id, group_participant__user__id=user_id))==2):
            return str(2)

        elif(len(PokerBoard.objects.filter(id=pokerboard_id,group_spectator__user__id=user_id))==1):
            if(len(Role.objects.filter(pokerboard_id=pokerboard_id, user_id=user_id, roles=2))==1):
                return str(2)
            else:
                return str(3)
        
        elif(len(PokerBoard.objects.filter(id=pokerboard_id,group_participant__user__id=user_id))==1):
            if(len(Role.objects.filter(pokerboard_id=pokerboard_id, user_id=user_id, roles=2))==1):
                return str(2)
            else:
                return str(3)
        
        else:
            if(len(Role.objects.filter(pokerboard_id=pokerboard_id, user_id=user_id))==1):
                return Role.objects.get(pokerboard_id=pokerboard_id, user_id=user_id).roles
