from django.db import transaction
from django.http import HttpResponse
from django.urls import reverse
from rest_framework import permissions, serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from planningpoker import settings
from planningpoker.tasks import send_accept_email_task, send_accept_email_task1
from pokerboard.models import (AcceptRequest, Group, InviteEmail, Issue,
                               PokerBoard, Role, UserCard)
from user.models import Token, UserInfo
from pokerboard.utils import get_current_role


class IssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Issue
        fields = ['issue_type', 'issue_summary', 'issue_description', 'id', 'issue_estimate','jira_id']
        read_only_fields = ['id', 'issue_estimate']

    def validate_jira_id(self, value):
        if value is None:
            return
        name = self.context['name']
        pobj = PokerBoard.objects.get(name=name)
        issues = Issue.objects.filter(pokerboard=pobj, jira_id=value)
        if len(issues)>0:
            raise serializers.ValidationError("Issue already exists", code=status.HTTP_400_BAD_REQUEST)
        return value

    
class PokerBoardSerializer(serializers.ModelSerializer):
    invite_email = serializers.ListField(child=serializers.EmailField(), write_only=True)
    issues = IssueSerializer(read_only=True, many=True,source="issue_set") 
    class Meta:
        model = PokerBoard
        fields = ['name', 'description', 'timer', 'card_set', 'card_limit', 'invite_email', 'custom_id', 'issues']
    
    
    def create(self, validated_data):
        user = self.context['request'].user
        emails = validated_data.pop('invite_email')
        email_ids = []
        obj =  super(PokerBoardSerializer, self).create(validated_data)
        for email in emails:
            email_obj = InviteEmail.objects.create(email=email)
            AcceptRequest.objects.create(invite_email=email_obj, pokerboard=obj)
            email_ids.append(email_obj.pk)  
            
        Role.objects.create(pokerboard=obj, user=user, roles=1)
        email_subject = "INVITATION FOR USER::"
        for email_id in email_ids:
            email_obj = InviteEmail.objects.get(id=email_id)
            url = settings.LOCAL_URL 
            try:
                user = UserInfo.objects.get(email=email_obj.email)
                send_accept_email_task.delay(email_subject, email_id, url)
            except UserInfo.DoesNotExist:
                send_accept_email_task.delay(email_subject, email_id, url)
        return obj


    def to_representation(self , instance):
        user = self.context['request'].user
        manager_obj = Role.objects.get(pokerboard__name=instance.name,roles=1)
        pokerboard_id = PokerBoard.objects.get(name=instance.name).id
        poker_list = super().to_representation(instance)
        if(manager_obj.user_id==user.id):
            poker_list['isManager'] = True
        else :
            poker_list['isManager'] = False
        role = get_current_role(pokerboard_id=pokerboard_id, user_id=user.id)
        poker_list['role'] = role
        poker_list['manager'] = manager_obj.user.first_name + " " + manager_obj.user.last_name
        if instance.card_set == 1:
            series = [1, 2]
            for i in range(2, 100):
                num = series[i-1] + series[i-2]
                if num > instance.card_limit:
                    break
                series.append(num)
            series.insert(0,0)
        elif instance.card_set == 2:
            series = range(1, instance.card_limit//2+1)
            series = [x*2 for x in series]
        elif instance.card_set == 3:
            series = range(1, instance.card_limit//2+1)
            series = [x*2-1 for x in series]
            series.insert(0,0)
        poker_list['series'] = series
        return poker_list


class GroupSerializer(serializers.ModelSerializer):
    user = serializers.ListField(child=serializers.EmailField(),write_only=True)

    class Meta:
        model = Group
        fields = ['user', 'name','description']
    
    def create(self,validated_data):
      
        users = validated_data.pop('user')
      
        user_ids = []
        
        for email in users:
            user_obj = UserInfo.objects.get(email=email)
            sid = transaction.savepoint()
            user_ids.append(user_obj.pk)
       
        validated_data['user'] = user_ids
        try:
            obj =  super(GroupSerializer,self).create(validated_data) 
            transaction.savepoint_commit(sid)
        except:
            transaction.savepoint_rollback(sid)
            raise TypeError("Error occured while creating Group object")

        return obj


class IssueEstimateSerializer(serializers.ModelSerializer):
    issue_estimate = serializers.IntegerField(source="issue.issue_estimate")
    class Meta:
        model = UserCard
        fields = ('card_selected', 'issue_estimate')


class EstimateSerializer(serializers.Serializer):
    
    id = serializers.IntegerField(read_only=True)
    issue_estimate = serializers.IntegerField()
    comment = serializers.CharField(max_length=None)
    pokerboard_name = serializers.CharField(write_only=True)

    def update(self, instance, validated_data):
        instance.issue_estimate = validated_data.get("issue_estimate",instance.issue_estimate)
        instance.comment = validated_data.get("comment", instance.comment)
        instance.save()
        return instance


class EditBoardUserSerializer(serializers.Serializer):
    users = serializers.ListField(child=serializers.EmailField(), write_only=True)
    role_users = serializers.IntegerField(write_only=True)
    pokerboard_name = serializers.CharField(write_only=True)
    
    def update(self, instance, validated_data):
        users = validated_data.pop('users')
        pokerboard_name = validated_data.pop('pokerboard_name')
        pokerboard_id = PokerBoard.objects.get(name=pokerboard_name).id
        role_users = validated_data.pop('role_users')

        email_subject = "INVITATION FOR USER:"
        user_ids = []
        
        for id in instance.user.all():
            user_ids.append(id)

        for user in users:
            user_obj = UserInfo.objects.get(email=user)
            if(len(Role.objects.filter(user_id=user_obj.id, pokerboard_id=pokerboard_id))==0):
                Role.objects.create(user_id=user_obj.id, pokerboard_id=pokerboard_id, roles=role_users)
            else:
                Role.objects.filter(user_id=user_obj.id, pokerboard_id=pokerboard_id).update(roles=role_users)
                    
    
            url = settings.LOCAL_URL + 'login/' 
            send_accept_email_task1.delay(email_subject, user_obj.email, url)

            user_ids.append(user_obj.pk)
        
        instance.user = user_ids
        instance.save()
        return instance


class EditBoardGroupSerializer(serializers.Serializer):
    group = serializers.ListField(child=serializers.CharField(), write_only=True)
    role_group = serializers.IntegerField(write_only=True)
    pokerboard_name = serializers.CharField(write_only=True)

    def update(self, instance, validated_data):
        groups = validated_data.pop('group')
        role_group = validated_data.pop('role_group')

        email_subject = "INVITATION FOR USER:"
        group_participant_ids = []
        group_spectator_ids = []

        for id in instance.group_spectator.all():
            group_spectator_ids.append(id)
        
        for id in instance.group_participant.all():
            group_participant_ids.append(id)
        
        if(role_group==2):
            # Participants
            for group in groups:
                group_obj = Group.objects.get(name=group)
                if(group_obj.pk in group_participant_ids):
                    pass
                else:
                    group_participant_ids.append(group_obj.pk)

                    for user in group_obj.user.all():
                        url = settings.LOCAL_URL + 'login/' 
                        send_accept_email_task1.delay(email_subject, user.email, url)
        else:
            # Spectator
            for group in groups:
                group_obj = Group.objects.get(name=group)
                if(group_obj.pk in group_participant_ids):
                    pass
                else:
                    group_spectator_ids.append(group_obj.pk)
                    for user in group_obj.user.all():
                        url = settings.LOCAL_URL + 'login/' 
                        send_accept_email_task1.delay(email_subject, user.email, url)

        instance.group_participant = group_participant_ids
        instance.group_spectator = group_spectator_ids
        instance.save()
        return instance


class DeleteBoardSerializer(serializers.Serializer):
    users = serializers.ListField(child=serializers.EmailField(), write_only=True)
    groups = serializers.ListField(child=serializers.CharField(), write_only=True)
    pokerboard_name = serializers.CharField(write_only=True)

    def update(self, instance, validated_data):
        users = validated_data.pop('users')
        groups = validated_data.pop('groups')
        pokerboard_name = validated_data.pop('pokerboard_name')
        pokerboard_id = PokerBoard.objects.get(name=pokerboard_name)

        delete_user_ids = []
        for user in users:
            user_id = UserInfo.objects.get(email=user).id
            delete_user_ids.append(user_id)
        
        user_ids = []
        for id in instance.user.all():
            if(id in delete_user_ids):
               Role.objects.filter(user_id=id, pokerboard_id=pokerboard_id).delete()
            else:
                user_ids.append(id)

        instance.user = user_ids 

        delete_group_ids = []
        for group in groups:
            group_id = Group.objects.get(name=group).id
            delete_group_ids.append(group_id)

        group_spectator_ids = []
        for id in instance.group_spectator.all():
            if(id in delete_group_ids):
               pass
            else:
                group_spectator_ids.append(id)
        
        group_participants_ids = []
        for id in instance.group_participant.all():
            if(id in delete_group_ids):
                pass
            else:
                group_participants_ids.append(id)
        
        instance.group_participant = group_participants_ids
        instance.group_spectator = group_spectator_ids

        instance.save()

        return instance
