"""models.py - This file contains the class definitions for the Datastore
entities used by the Game. Because these classes are also regular Python
classes they can include methods (such as 'to_form' and 'new_game')."""

import random
from datetime import date
from protorpc import messages
from google.appengine.ext import ndb
import logging
import json
wordDict = ['EATING','NATURE','LINEAR','RETINA','EARING','TINDER','TAILOR']

class User(ndb.Model):
    """User profile"""
    name = ndb.StringProperty(required=True)
    email =ndb.StringProperty()
    won = ndb.IntegerProperty(required=True,default=0)
    loss = ndb.IntegerProperty(required=True,default=0)
    win_percent = ndb.IntegerProperty(required=True,default=0)


class Game(ndb.Model):
    """Game object"""
    target = ndb.StringProperty(required=True)
    attempts_allowed = ndb.IntegerProperty(required=True)
    attempts_remaining = ndb.IntegerProperty(required=True, default=5)
    game_over = ndb.BooleanProperty(required=True, default=False)
    user = ndb.KeyProperty(required=True, kind='User')
    user_name = ndb.StringProperty(required=True )
    guess = ndb.StringProperty(required=True)
    history = ndb.StringProperty(required = True)

    @classmethod
    def new_game(cls, user,key,user_name):
        """Creates and returns a new game"""
        game = Game(user=user,
                    user_name = user_name,
                    target=wordDict[random.choice(range(0, 7))],
                    attempts_allowed=10,
                    attempts_remaining=10,
                    guess = '------',
                    key = key,
                    history = json.dumps([]),
                    game_over=False)
        game.put()
        return game

    def to_form(self, message):
        """Returns a GameForm representation of the Game"""
        form = GameForm()
        form.urlsafe_key = self.key.urlsafe()
        form.user_name = self.user.get().name
        form.attempts_remaining = self.attempts_remaining
        form.game_over = self.game_over
        form.message = message
        form.guess = self.guess
        return form

    def end_game(self, won=False,user_name=None,guesses=None):
        """Ends the game - if won is True, the player won. - if won is False,
        the player lost. also updates the player score win/loss guesses and win percentage"""
        self.game_over = True
        self.put()
        key = ndb.Key( User,user_name ).get()
        q = key
        if(won):
            q.won += 1
        else:
            q.loss += 1
        
        tot = q.won+q.loss
        if(q.won != 0):
            q.win_percent =  (q.won/tot) * 100
        q.put()
        # return        

    def store_move(self ,message=None,game=None,guess=None):
        """ store each move for game history """
        hist = json.loads(game.history)
        hist.append( (guess,message) )
        game.history = json.dumps(hist)
        game.put()

class Score(ndb.Model):
    """Score object"""
    user = ndb.StringProperty(required=True)
    won = ndb.BooleanProperty(required=True)
    guesses = ndb.IntegerProperty(required=True)

    def to_form(self):
        return ScoreForm(user_name=self.user.get().name, won=self.won,
                         date=str(self.date), guesses=self.guesses)


class GameForm(messages.Message):
    """GameForm for outbound game state information"""
    urlsafe_key = messages.StringField(1, required=True)
    attempts_remaining = messages.IntegerField(2, required=True)
    game_over = messages.BooleanField(3, required=True)
    message = messages.StringField(4, required=True)
    user_name = messages.StringField(5, required=True)
    guess = messages.StringField(6, required=True)


class NewGameForm(messages.Message):
    """Used to create a new game"""
    user_name = messages.StringField(1, required=True)
    # attempts = messages.IntegerField(2, default=5)
    # guess = messages.StringField(3,default="------")



class MakeMoveForm(messages.Message):
    """Used to make a move in an existing game"""
    guess = messages.StringField(1, required=True)

class Get_User_Name(messages.Message):
    """Form for inbound user name"""
    user_name = messages.StringField(1, required=True)

class ScoreForm(messages.Message):
    """ScoreForm for outbound Score information"""
    user_name = messages.StringField(1, required=True)
    date = messages.StringField(2, required=True)
    won = messages.BooleanField(3, required=True)
    guesses = messages.IntegerField(4, required=True)


class ScoreForms(messages.Message):
    """Return multiple ScoreForms"""
    items = messages.MessageField(ScoreForm, 1, repeated=True)


class StringMessage(messages.Message):
    """StringMessage-- outbound (single) string message"""
    message = messages.StringField(1, required=True)

class USER_GAMES(messages.Message):
   """outbound incomplete games of user """
   response = messages.StringField(1,repeated=True)

class DELETE_GAMES(messages.Message):
    """ Outbound success message for deleting game """
    response = messages.StringField(1)

class high_score(messages.Message):
    """ Outbound high score json as string  """
    response = messages.StringField(1)