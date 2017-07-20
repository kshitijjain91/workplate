from flask_mail import Message
from __init__ import app, mail
from flask import render_template
from config import ADMINS

def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    mail.send(msg)

def invite_mail(invitee_email, inviter_email):
    send_email("{0} has invited you to join workplate".format(inviter_email),
               ADMINS[0],
               [invitee_email],
               'text body', 'html body')
               # render_template("inviter_email.txt", invitee_email=invitee_email, inviter_email=inviter_email),
               # render_template("inviter_email.html", invitee_email=invitee_email, inviter_email=inviter_email))