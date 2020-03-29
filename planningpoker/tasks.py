import json

import requests
from celery import task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from requests.auth import HTTPBasicAuth

from planningpoker.settings import JIRA_HOST_EMAIL, JIRA_HOST_PASSWORD
from pokerboard.models import InviteEmail

from . import settings


def send_verify_email(email_subject, email, token):
    msg_html = render_to_string('templates/email_template.html', {'token': token, 'url': settings.URL})
    msg = ""
    send_mail(
        email_subject,
        msg,
        settings.EMAIL_HOST_USER,
        [email],
        html_message=msg_html
    )

def send_invite_email(email_subject, email, url):
    msg_html = render_to_string('templates/email_invite_template.html', { 'url': url })
    msg = ""
    send_mail(
        email_subject,
        msg,
        settings.EMAIL_HOST_USER,
        [email],
        html_message=msg_html
    )

# This is the decorator which a celery worker uses
@task()
def send_accept_email_task(email_subject, email_id, url):
    email_obj = InviteEmail.objects.get(pk=email_id)
    return send_invite_email(email_subject, email_obj.email, url)

@task()
def send_accept_email_task1(email_subject, email, url):
    return send_invite_email(email_subject, email, url)
    
@task()
def send_verify_email_task(email_subject, email, token):
    return send_verify_email(email_subject, email, token)

@task()
def notify_user(jira_id, customId, comment, estimate):
    url = 'https://ireflect.atlassian.net/rest/api/2/issue/'+str(jira_id)
    comment_url = url+'/comment' 
    payload = json.dumps( { "body": comment } )
    payload1 = json.dumps({
       "fields": {
           customId: estimate
        }
    })
    auth=(JIRA_HOST_EMAIL, JIRA_HOST_PASSWORD)
   
    headers = { "Accept": "application/json",
                "Content-Type": "application/json" }
    r = requests.post(comment_url, data=payload,  auth=auth, headers=headers)
    print(url, customId, payload1)
    r1 = requests.put(url, data=payload1,  auth=auth, headers=headers)
    print(r)
    print(r1)
