from django.shortcuts import render
from rest_framework import permissions, status, viewsets
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from user.models import Token, UserInfo
from user.serializers import LoginSerializer, SignUpSerializer


class SignupViewSet(viewsets.ModelViewSet):
    serializer_class = SignUpSerializer
    queryset = UserInfo.objects.all()


class GetUserView(RetrieveAPIView):
    """
    Provides the user details of a user from its token
    """
    permission_classes = [permissions.IsAuthenticated, ]
    def get(self, request, *args, **kwargs):
        user = request.user
        user = {
            "id": user.pk,
            "firstName": user.first_name,
            "lastName": user.last_name,
            "isActive": user.verified,
            "email": user.email
        }
        return Response(user)


class LoginViewSet(APIView):
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token = Token.objects.get_or_create(user=user)[0]
        return Response(
            {
                'token': token.key
            }
        )


class EmailVerify(APIView):

    def get(self, request, pk=None):
        token = request.GET.get('token')

        try:
            user = UserInfo.objects.get(email_token=token)
            if(user.verified == True):
                return Response({'message': 'User already verified'}, status=status.HTTP_200_OK)
        except:
            response = {
                'error': 'Invalid Key!'
            }
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        if not token:
            return Response({'error': 'Invalid URL'}, status=status.HTTP_400_BAD_REQUEST)

        user.verified = True
        user.save()
        return Response({'message': 'Verified Success'}, status=status.HTTP_200_OK)
