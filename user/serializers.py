import uuid

from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from rest_framework import serializers

from planningpoker import settings
from planningpoker.tasks import send_accept_email_task, send_verify_email_task
from pokerboard.models import AcceptRequest, InviteEmail, PokerBoard, Role
from user.models import UserInfo


class SignUpSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserInfo
        fields = ['email', 'first_name', 'last_name', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        password = validated_data.get('password')
        email = validated_data.get('email')
        instance = super(SignUpSerializer, self).create(validated_data)
        email_subject = "PlanningPoker Email Verification"

        if password is not None:
            instance.set_password(password)
            emailtoken = uuid.uuid4()
            instance.email_token = emailtoken
            token = str(emailtoken)
            send_verify_email_task.delay(email_subject, email, token)
            instance.save()
            return instance


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(label="EMAIL")
    password = serializers.CharField(label="Password", style={
                                     'input_type': 'password'}, trim_whitespace=False)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(email=email, password=password)

            if not user:
                msg = ['Unable to Login with Provided Credentials.']
                raise serializers.ValidationError(msg, code='authorization')
            else:
                if user.verified == False:
                    msg = ['Please verify your Email Id. ']
                    raise serializers.ValidationError(
                        msg, code='authorization')
                else:
                    attrs['user'] = user
                    try:
                        email_obj = InviteEmail.objects.get(email=email)
                        if PokerBoard.objects.filter(invite_email=email_obj).exists():
                            pokerqs = PokerBoard.objects.filter(
                                invite_email=email_obj)
                            for pokerobj in pokerqs:
                                email_subject = "INVITATION FOR USER:"
                                url = settings.LOCAL_URL + 'pokerboard/' + pokerobj.name
                                try:
                                    role = Role.objects.get(
                                        pokerboard=pokerobj, user=user)
                                except Role.DoesNotExist:
                                    Role.objects.create(
                                        pokerboard=pokerobj, user=user, roles=2)
                                    
                    except InviteEmail.DoesNotExist:
                        return attrs
                    return attrs
