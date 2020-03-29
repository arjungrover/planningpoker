import base64
import json

import requests
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from requests.auth import HTTPBasicAuth
from rest_framework import permissions, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from planningpoker.settings import (JIRA_HOST_EMAIL, JIRA_HOST_PASSWORD,
                                    JIRA_SEARCH_URL)
from planningpoker.tasks import notify_user
from pokerboard.models import (AcceptRequest, Group, InviteEmail, Issue,
                               PokerBoard, Role, UserCard)
from pokerboard.serializers import (DeleteBoardSerializer,
                                    EditBoardGroupSerializer,
                                    EditBoardUserSerializer,
                                    EstimateSerializer, GroupSerializer,
                                    IssueEstimateSerializer, IssueSerializer,
                                    PokerBoardSerializer)
from user.models import Token


class GroupViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, ]
    serializer_class = GroupSerializer
    queryset = Group.objects.all()
    

class PokerboardViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, ]
    serializer_class = PokerBoardSerializer
    
    def list(self, request):
        user = request.user
        name = request.query_params.get('name')
        name = name.replace("+", " ")
        poker = PokerBoard.objects.get(name=name)
        serializer = PokerBoardSerializer(poker, context={'request':request})
        return Response(serializer.data)


class CreateIssues(CreateAPIView):
    
    def post(self, request, *args, **kwargs):
        name = request.data['name']
        name = name.replace("+", " ")
        pokerboard = PokerBoard.objects.get(name=name)
        stories = request.data['stories']
        serializer = IssueSerializer(data=stories, many=True, context={'name': name})
        serializer.is_valid(raise_exception=True)
        serializer.save(pokerboard=pokerboard)
        return Response({'created'}, status=status.HTTP_200_OK)


class GetJiraSearchResult(ListAPIView):
    
    def get(self, request, *args, **kwargs):
        search = request.query_params.get('search')
        url = JIRA_SEARCH_URL + search 
        try:
            response = requests.get(url, auth=(JIRA_HOST_EMAIL, JIRA_HOST_PASSWORD))
            response = response.json()
            issues = []
            count = 0
            for issue in response["issues"]:
                issues.append({
                "index": count,
                "id": issue["id"],
                "key": issue["key"],
                "summary": issue["fields"]["summary"],
                "description": issue["fields"]["description"]
                })
                count = count + 1
        except:
            message = response["errorMessages"]
            error =  str(message)
            return Response(error,status=status.HTTP_400_BAD_REQUEST)
        return Response(issues)


class GetEstimates(ListAPIView):
    permission_classes = [permissions.IsAuthenticated,]
    serializer_class = IssueEstimateSerializer
   
    def get(self, request, *args, **kwargs):
        user = request.user
        qs = UserCard.objects.filter(user=user)
        data = IssueEstimateSerializer(qs, many=True).data
        return Response(data, status=status.HTTP_200_OK)


class AcceptView(APIView):
    
    def post(self, request):
        poker_id = request.data['poker_id']
        email_id = request.data['email_id']
        accepted = request.data['accept']
        
        try:
            user = AcceptRequest.objects.get(
                pokerboard=poker_id, invite_email=email_id)
            if(user.is_visited == True):
                return Response({'msg': 'You have already submitted your response'}, status=status.HTTP_400_BAD_REQUEST)
        except:
            response = {
                'error': 'Invalid ID!'
            }
            return Response(response, status=status.HTTP_400_BAD_REQUEST)


        if(accepted):
            user.is_visited = True
            user.accept_request = True
            user.save()
            return Response({'message': 'REQUEST ACCEPTED'}, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'REQUEST REJECTED'}, status=status.HTTP_200_OK)



class GetAllPokerboards(RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated, ]
    """
    Returns all pokerboards related to a user.
    except:
            return Response({"Error"}, status=status.HTTP_400_BAD_REQUEST)

    """
    def get(self, request, *args, **kwargs):
        user = request.user
        roles_qs = Role.objects.filter(user=user)
        pokerboardList = []
        for role in roles_qs:
            poker_obj = PokerBoard.objects.get(pk=role.pokerboard.pk)
            issues = Issue.objects.filter(pokerboard=poker_obj)
            issue_list = IssueSerializer(issues, many=True)

            pokerboardList.append({
                "name": poker_obj.name,
                "description": poker_obj.description,
                "issueList": issue_list.data
            })
        return Response(pokerboardList)


class GetGroupNames(ListAPIView):
    serializer_class = GroupSerializer
    def get_queryset(self):
        queryset = Group.objects.all()
        return queryset


class EstimateView(APIView):
    permission_classes = [permissions.IsAuthenticated, ]
    def patch(self, request, pk, format=None):
        
        issue_obj = Issue.objects.get(id=pk)
        
        serializer = EstimateSerializer(issue_obj, data = request.data)
        if serializer.is_valid():
            if issue_obj.jira_id is not None:
                pokerboard_name = request.data["pokerboard_name"]
                pokerboard_id = PokerBoard.objects.get(name=pokerboard_name).id
                custom_id = PokerBoard.objects.get(id=pokerboard_id).custom_id
                notify_user.delay(issue_obj.jira_id, custom_id, request.data["comment"], request.data["issue_estimate"])
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EditBoardUserView(APIView):
    permission_classes = [permissions.IsAuthenticated, ]
    def patch(self, request, format=None):
    
        pokerboard_obj = PokerBoard.objects.get(name=request.data['pokerboard_name'])
        serializer = EditBoardUserSerializer(pokerboard_obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.data, status=status.HTTP_400_BAD_REQUEST)


class EditBoardGroupView(APIView):
    permission_classes = [permissions.IsAuthenticated, ]
    def patch(self, request, format=None):
    
        pokerboard_obj = PokerBoard.objects.get(name=request.data['pokerboard_name'])
        serializer = EditBoardGroupSerializer(pokerboard_obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.data, status=status.HTTP_400_BAD_REQUEST)


class DeleteBoardView(APIView):
    permission_classes = [permissions.IsAuthenticated, ]
    def patch(self, request,format=None):

        pokerboard_obj = PokerBoard.objects.get(name=request.data['pokerboard_name'])
        serializer = DeleteBoardSerializer(pokerboard_obj, data=request.data)
        if serializer.is_valid():
            serializer.save()

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
