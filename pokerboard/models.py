from collections import namedtuple

from django.db import models

from base.models import BaseModel
from user.models import UserInfo


class InviteEmail(BaseModel, models.Model):
    """
    This model will store all information related to invite emails
    """
    email = models.EmailField(verbose_name="Invite Emails", max_length=255)

    def __str__(self):
        return self.email


class Group(BaseModel, models.Model):
    """
    This model will be used to group users together 
    """
    name = models.CharField(verbose_name="Group Name",
                            max_length=50, unique=True)
    user = models.ManyToManyField(UserInfo, related_name="users")
    description = models.TextField(verbose_name="Description", blank=False)

    def __str__(self):
        return self.description


class PokerBoard(BaseModel, models.Model):
    """
    This model will store all information related to pokerboard
    """
    TYPE = namedtuple('TYPE', ['FIBONACCI', 'EVEN', 'ODD'])(
        FIBONACCI=1,
        EVEN=2,
        ODD=3
    )
    CARD_TYPE = [
        (TYPE.FIBONACCI, 'Fibonacci'),
        (TYPE.EVEN, 'Even'),
        (TYPE.ODD, 'Odd')]

    name = models.CharField(
        verbose_name="PokerBoard Name", max_length=50, unique=True)
    description = models.TextField(
        verbose_name="PokerBoard Description", blank=True)
    total_estimate = models.PositiveIntegerField(
        verbose_name="PokerBoard Estimate", default=0)
    timer = models.PositiveIntegerField(
        verbose_name="PokerBoard Timer", default=0)
    card_set = models.PositiveIntegerField(
        verbose_name="Card Set", choices=CARD_TYPE)
    card_limit = models.PositiveIntegerField(blank=False)
    game_id = models.CharField(verbose_name="Current Playing Game",
                               max_length=255, unique=True, null=True, blank=True)
    invite_email = models.ManyToManyField(InviteEmail, through='AcceptRequest')
    current_issue_id = models.IntegerField(null=True, blank=True)
    start_time = models.DateTimeField(null=True, blank=True)
    group_spectator = models.ManyToManyField(Group, related_name="spectators")
    group_participant = models.ManyToManyField(
        Group, related_name="participants")
    user = models.ManyToManyField(UserInfo)
    custom_id = models.TextField(null=True, blank=True)

    def __str__(self):
        return "{} : {}".format(self.name, self.description)


class AcceptRequest(BaseModel, models.Model):
    """
    Model for accept and reject email requests
    """
    is_visited = models.BooleanField(default=False)
    accept_request = models.BooleanField(default=False)
    pokerboard = models.ForeignKey(
        PokerBoard, on_delete=models.CASCADE, null=True)
    invite_email = models.ForeignKey(InviteEmail, on_delete=models.CASCADE)


class Role(BaseModel, models.Model):
    """
    This model will store all information related to CurrentRoles of the user
    """
    TYPE = namedtuple('TYPE', ['MANAGER', 'PARTICIPANT', 'SPECTATOR'])(
        MANAGER=1,
        PARTICIPANT=2,
        SPECTATOR=3
    )
    ROLE_TYPE = [
        (TYPE.MANAGER, 'Manager'),
        (TYPE.PARTICIPANT, 'Participant'),
        (TYPE.SPECTATOR, 'Spectator')]

    pokerboard = models.ForeignKey(
        PokerBoard, on_delete=models.CASCADE, null=False)
    user = models.ForeignKey(UserInfo, null=False, on_delete=models.CASCADE)
    roles = models.PositiveIntegerField(choices=ROLE_TYPE)
    has_participated = models.BooleanField(default=False)
    has_accepted = models.BooleanField(default=False)

    def __str__(self):
        return "{} : {}".format(self.pokerboard_id, self.user)


class Issue(BaseModel, models.Model):
    """
    This model will store all information related to Issues created at pokerboard 
    """
    issue_type = models.CharField(verbose_name="Issue Type", max_length=20)
    issue_summary = models.CharField(
        verbose_name="Issue Summary", max_length=255)
    issue_description = models.TextField(
        verbose_name="Issue Description", blank=True)
    pokerboard = models.ForeignKey(
        PokerBoard, on_delete=models.CASCADE, null=False)
    issue_estimate = models.PositiveIntegerField(default=0)
    comment = models.TextField(verbose_name="Comment", blank=True)
    jira_id = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return "{} : {}".format(self.issue_type, self.issue_description)


class UserEstimate(BaseModel, models.Model):
    """
    This model will store all information related to Estimations given by participants
    """
    user = models.ForeignKey(UserInfo, on_delete=models.CASCADE, null=False)
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, null=False)
    user_estimate = models.PositiveIntegerField(
        verbose_name="User Estimate", default=0)
    response_time = models.DurationField(verbose_name="Response Time")

    def __str__(self):
        return "{} : {}".format(self.user, self.user_estimate)


class Player(BaseModel, models.Model):
    """
    This model will be used to provide Live Users during gameplay
    """
    room_id = models.CharField(verbose_name="Room id", max_length=255)
    user = models.ForeignKey(UserInfo, on_delete=models.CASCADE, null=False)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return self.room_id


class UserCard(BaseModel, models.Model):
    """
    This model will be used to show selected card
    """
    room_id = models.CharField(verbose_name="Room id", max_length=255)
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, null=False)
    user = models.ForeignKey(UserInfo, on_delete=models.CASCADE, null=False)
    card_selected = models.PositiveIntegerField(verbose_name="Selected Card")

    def __str__(self):
        return self.room_id
