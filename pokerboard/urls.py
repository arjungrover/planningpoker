from django.conf.urls import url
from django.contrib import admin
from rest_framework import routers
from pokerboard.views import PokerboardViewSet, AcceptView, GetAllPokerboards, CreateIssues, GetJiraSearchResult, GetGroupNames, GetEstimates, EstimateView, GroupViewSet, EditBoardUserView, DeleteBoardView, EditBoardGroupView

urlpatterns = [
    url(r'^accept/post/$', AcceptView.as_view(), name="accept"),
    url(r'^get-pokerboards/$', GetAllPokerboards.as_view()),
    url(r'^create-issues/$', CreateIssues.as_view()),
    url(r'^jira-search-result/$', GetJiraSearchResult.as_view()),
    url(r'^get-group-names/$', GetGroupNames.as_view()),
    url(r'get-estimates/$', GetEstimates.as_view()),
    url(r'^set-estimates/(?P<pk>\d+)/$', EstimateView.as_view()),
    url(r'^add-user', EditBoardUserView.as_view()),
    url(r'^add-group', EditBoardGroupView.as_view()),
    url(r'^delete-pokerboard', DeleteBoardView.as_view()),
]

router = routers.SimpleRouter()
router.register(r'pokerboard-form', PokerboardViewSet, basename="poker-form")
router.register(r'create-group',GroupViewSet)
urlpatterns +=router.urls
