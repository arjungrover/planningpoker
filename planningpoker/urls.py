from django.conf.urls import include, url
from django.contrib import admin
from rest_framework import routers

from pokerboard import views
from pokerboard.views import GroupViewSet
from user.views import EmailVerify, GetUserView, LoginViewSet, SignupViewSet

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^login/', LoginViewSet.as_view(), name="login"),
    url(r'', include('pokerboard.urls')),
    url(r'^verify/', EmailVerify.as_view(), name="verify"),
    url(r'^get-user/$', GetUserView.as_view()),
]

router = routers.SimpleRouter()
router.register(r'signup', SignupViewSet, basename="signup")
urlpatterns = urlpatterns + router.urls

router.register(r'group',GroupViewSet)
urlpatterns = urlpatterns + router.urls

obtain_auth_token = LoginViewSet.as_view()
