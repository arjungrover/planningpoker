import json
import uuid

from channels import Group
from channels.sessions import channel_session
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from pokerboard.models import Player, PokerBoard, Role, UserCard
from user.models import Token, UserInfo


def is_manager(logged_user_id, pokerboard_id):
    """
    This method returns if the user is a manager on current pokerboard or not.
    """
    manager_id = Role.objects.get(pokerboard_id=pokerboard_id, roles=1).user_id
    return logged_user_id == manager_id


def ws_connect(message, *args, **kwargs):
    """
    This function is called whenever a client tries to connect.
    """
    pokerboard_name = kwargs['name']
    pokerboard_name = pokerboard_name.replace("+", " ")
    token = kwargs['token']

    logged_user_id = Token.objects.get(key=token).user_id

    pokerboard_obj = PokerBoard.objects.get(name=pokerboard_name)

    if pokerboard_obj.game_id is None:
        if not is_manager(logged_user_id, pokerboard_obj.id):
            # Access Denied
            message.reply_channel.send({
                "text": 'ACCESS DENIED', "close": True
            })

        else:
            pokerboard_obj.game_id = uuid.uuid1()
            pokerboard_obj.save()
            # Manager Room Created
            message.reply_channel.send({
                "accept": True
            })
            if pokerboard_obj.start_time is not None:
                time_left = timezone.now() - pokerboard_obj.start_time
                Group(str(pokerboard_obj.game_id)).send(
                    {"text": json.dumps({"timeleft": time_left.__str__()})})

            Group(str(pokerboard_obj.game_id)).add(message.reply_channel)

            player_obj = Player.objects.get_or_create(
                room_id=pokerboard_obj.game_id, user_id=logged_user_id)[0]
            player_obj.is_active = True
            player_obj.save()
            live = list(Player.objects.filter(room_id=pokerboard_obj.game_id,
                                               is_active=True).values_list('user__first_name', flat=True))
            Group(str(pokerboard_obj.game_id)).send(
                {"text": json.dumps({"type": "online Player", "list": live})})
            
    else:
        player_obj = Player.objects.get_or_create(
            room_id=pokerboard_obj.game_id, user_id=logged_user_id)[0]
        player_obj.is_active = True
        player_obj.save()
        message.reply_channel.send({"accept": True})
        live = list(Player.objects.filter(room_id=pokerboard_obj.game_id,
                                           is_active=True).values_list('user__first_name', flat=True))
        Group(str(pokerboard_obj.game_id)).add(message.reply_channel)
        message.reply_channel.send(
            {"text": json.dumps({"type": "online Player", "list": live})})
        Group(str(pokerboard_obj.game_id)).send({"text": json.dumps(
            {"type": "online Player", "list": live})}, immediately=True)
        

def ws_disconnect(message, *args, **kwargs):
    
    pokerboard_name = kwargs['name']
    pokerboard_name = pokerboard_name.replace("+", " ")
    token_key = kwargs['token']

    logged_user_id = Token.objects.get(key=token_key).user_id
    pokerboard_obj = PokerBoard.objects.get(name=pokerboard_name)

    if(is_manager(logged_user_id, pokerboard_obj.id)):
        Player.objects.filter(
            room_id=pokerboard_obj.game_id, is_active=True).update(is_active=False)

        Group(str(pokerboard_obj.game_id)).discard(message.reply_channel)
        Group(str(pokerboard_obj.game_id)).send({"text": "Session Over!!"})
        pokerboard_obj.game_id = None
        pokerboard_obj.current_issue_id = None
        pokerboard_obj.start_time = None
        pokerboard_obj.save()
        message.reply_channel.send({"close": True})

    else:

        Player.objects.filter(user_id=logged_user_id).update(is_active=False)
        Group(str(pokerboard_obj.game_id)).discard(message.reply_channel)
        live = list(Player.objects.filter(room_id=pokerboard_obj.game_id,
                                           is_active=True).values_list('user__first_name', flat=True))
        Group(str(pokerboard_obj.game_id)).send(
            {"text": json.dumps({"type": "online Player", "list": live})})
        message.reply_channel.send({"close": True})


def card_chosen(message, name, value, issue_id, token, **kwargs):
    """
    When message for Card chosen is called, it should be reflected to all users.
    """

    logged_user_id = Token.objects.get(key=token).user_id
    room_id = PokerBoard.objects.get(name=name).game_id

    # update card
    if(len(UserCard.objects.filter(room_id=room_id, issue_id=issue_id, user_id=logged_user_id)) == 0):
        UserCard.objects.create(
            room_id=room_id, issue_id=issue_id, user_id=logged_user_id, card_selected=value)

    else:
        UserCard.objects.filter(room_id=room_id, issue_id=issue_id,
                                user_id=logged_user_id).update(card_selected=value)

    queryset = UserCard.objects.filter(room_id=room_id, issue_id=issue_id)

    cards = []
    for each in queryset:
        obj = Player.objects.get(user_id=each.user.id, room_id=room_id)
        if (obj.is_active == True):
            user_name = "{first_name} {last_name}".format(
                first_name=each.user.first_name, last_name=each.user.last_name)
            cards.append({"user": user_name, "card": each.card_selected})

    Group(str(room_id)).send({
        "text": json.dumps({"type": "card list", "cards": cards})
    })


def change_issue(message, name, issue_id, **kwargs):
    """
    When message for Change issue is called, it should be reflected to all users.
    """
    pobj = PokerBoard.objects.get(name=name)
    pobj.current_issue_id = issue_id
    pobj.save()
    message.reply_channel.send({"accept": True})
    Group(str(pobj.game_id)).send({
        "text": json.dumps({"change": issue_id})})


def start_game(message, name, **kwargs):
    """
    When a player or spectator joins game, this method is called.
    """
    pobj = PokerBoard.objects.get(name=name)
    if pobj.current_issue_id is not None:
        message.reply_channel.send(
            {"text": json.dumps({"issue_id": pobj.current_issue_id})})
    if pobj.start_time is not None:
        time_left = timezone.now() - pobj.start_time
        Group(str(pobj.game_id)).send(
            {"text": json.dumps({"timeleft": time_left.__str__()})})
    live = list(Player.objects.filter(room_id=pobj.game_id,
                                       is_active=True).values_list('user__first_name', flat=True))
    Group(str(pobj.game_id)).send({"text": json.dumps(
        {"type": "online Player", "list": live})}, immediately=True)


def timer_start(message, name, **kwargs):
    """
    When message for Start timer is called, it should be reflected to all users.
    """
    pokerobj = PokerBoard.objects.get(name=name)
    pokerobj.start_time = timezone.now()
    pokerobj.save()
    Group(str(pokerobj.game_id)).send(
        {"text": json.dumps({"startTimer": True})})


def ws_message(message, name, token, *args, **kwargs):
    """
    Recieves messages from the clients
    """
    get_message = json.loads(message.content['text'])
    
    data = get_message['data'] if 'data' in get_message else {}
    name = name.replace("+", " ")

    switch = {
        'cardChosen': card_chosen,
        'startGame': start_game,
        'changeIssue': change_issue,
        'startTimer': timer_start
    }
    function = switch.get(get_message['type'])
    return function(message, name, token=token, **data)
