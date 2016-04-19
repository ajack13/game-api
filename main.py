#!/usr/bin/env python

"""main.py - This file contains handlers that are called by taskqueue and/or
cronjobs."""
import logging

import webapp2
from google.appengine.api import mail, app_identity
from api import hangman

from models import User,Game


class SendReminderEmail(webapp2.RequestHandler):
    def get(self):
        """Send a reminder email to User with unfinished games.
        Called every hour using a cron job"""
        app_id = app_identity.get_application_id()
        users = User.query(User.email != None)
        games = Game.query(Game.game_over == False)
        userData = {}
        # create a dict of key:user_name value:user_email
        for user in users:
            userData[user.name] = user.email
        # check each user for unfinished game and send a mail
        for game in games:
            if game.user_name in userData:
                subject = 'This is a reminder!'
                body = 'Hello {}, try out Guess A Number!'.format(game.user_name)
                # This will send test emails, the arguments to send_mail are:
                # from, to, subject, body
                mail.send_mail('noreply@{}.appspotmail.com'.format(app_id),
                           userData[game.user_name],
                           subject,
                           body)



app = webapp2.WSGIApplication([
    ('/crons/send_reminder', SendReminderEmail)
], debug=True)
