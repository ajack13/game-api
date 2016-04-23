"""api.py - Create and configure the Game API exposing the resources.
This can also contain game logic. For more complex games it would be wise to
move game logic to another file. Ideally the API will be simple, concerned
primarily with communication to/from the API's users."""
# ---------------------------------------------------------------------
# filename : api.py
# contains code for all endpoints of the app
# creator : ajay
# date : 28 feb 2015
# version 1.0
#----------------------------------------------------------------------

import logging
import endpoints
from protorpc import remote, messages
from google.appengine.api import memcache
from google.appengine.api import taskqueue
import json

from models import User, Game,Score
from models import StringMessage, NewGameForm , GameForm , MakeMoveForm, ScoreForms
from models import USER_GAMES,Get_User_Name,DELETE_GAMES,high_score
from utils import get_by_urlsafe
from google.appengine.ext import ndb

#request_messages
NEW_GAME_REQUEST = endpoints.ResourceContainer(NewGameForm)
MAKE_MOVE_REQUEST = endpoints.ResourceContainer(MakeMoveForm,
                      urlsafe_game_key=messages.StringField(1),)
USER_REQUEST = endpoints.ResourceContainer(user_name=messages.StringField(1),
                                           email=messages.StringField(2))
get_user_name = endpoints.ResourceContainer(user_name=messages.StringField(1))
set_limit = endpoints.ResourceContainer(limit=messages.IntegerField(1))
GET_HISTORY = endpoints.ResourceContainer(urlsafe_game_key=messages.StringField(1))
CANCEL_GAME = endpoints.ResourceContainer(urlsafe_game_key=messages.StringField(1))
MEMCACHE_MOVES_REMAINING = 'MOVES_REMAINING'
GET_GAME_REQUEST = endpoints.ResourceContainer(
        urlsafe_game_key=messages.StringField(1),)

''' 
     api_endpoint : hangman 
     contains all endpoints 
'''
@endpoints.api(name='game_api', version='v1')
class hangman(remote.Service):
    """Game API"""
    ''' 
     endpoint function : Create a user  
     path : user
     name : create_user
     returns  
     message : user created
    '''
    @endpoints.method(request_message=USER_REQUEST,
                      response_message=StringMessage,
                      path='user',
                      name='create_user',
                      http_method='POST')
    def create_user(self, request):
        """Create a User. Requires a unique username"""
        # check if user already created
        if User.query(User.name == request.user_name).get():
            raise endpoints.ConflictException(
                    'A User with that name already exists!')
        p_key = ndb.Key(User,request.user_name)
        # add user details
        user = User(name = request.user_name, email = request.email ,won=0,
                    loss=0,win_percent=0, key = p_key)
        user.put()
        
        s_key = ndb.Key(Score,request.user_name)
        # enter score entity for the user 
        # score = Score(won=0,lost=0,guesses=0,win_percent=0,
        #                 user=request.user_name,key=s_key)
        # score.put()
        return StringMessage(message='User {} created!'.format(
                request.user_name))

    ''' 
     create new game for the user 
     path : game
     name : new_game
     returns  
     user information and url_safe key for the game
    '''
    @endpoints.method(request_message=NEW_GAME_REQUEST,
                      response_message=GameForm,
                      path='game',
                      name='new_game',
                      http_method='POST')
    def new_game(self, request):
        """Creates new game"""
        user = User.query(User.name == request.user_name).get()
        
        p_key = ndb.Key(User,user.name)
        c_id = Game.allocate_ids(size = 1 , parent=p_key)[0]
        c_key = ndb.Key(Game , c_id ,parent=p_key)
        # check if user is registered
        if not user:
            raise endpoints.NotFoundException(
                    'A User with that name does not exist!')
        # register game in the datastore
        try:
            game = Game.new_game(user.key,c_key,user.name)
        except ValueError:
            raise endpoints.BadRequestException('Maximum must be greater '
                                                'than minimum!')

        # Use a task queue to update the average attempts remaining.
        # This operation is not needed to complete the creation of a new game
        # so it is performed out of sequence.
        # taskqueue.add(url='/tasks/cache_average_attempts')
        return game.to_form('Good luck playing hangman')

     
    ''' 
     get specific game from datastore 
     path : game
     name : get_game
     returns  
     game information
    '''
    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='get_game',
                      http_method='GET')
    def get_game(self, request):
        """Return the current game state."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            return game.to_form('Game retrieved !')
        else:
            raise endpoints.NotFoundException('Game not found!')

    ''' 
     make move (guess an alpahbet or the word) 
     name : make_move
     returns  
     game over | invalid entry | correct guess | you win 
    '''
    @endpoints.method(request_message=MAKE_MOVE_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='make_move',
                      http_method='PATCH')
    def make_move(self, request):
        """Makes a move. Returns a game state with message"""
        # get game with url_safe key
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        
        p_key = ndb.Key(Game,game.user_name)
        c_id = Score.allocate_ids(size = 1 , parent=p_key)[0]
        s_key = ndb.Key(Score , c_id ,parent=p_key)
        # s_key = ndb.Key(Game,game.user_name) 
        
        # check if user has run out of attempts
        if game.attempts_remaining < 1:
            game.end_game(won=False,user_name=game.user_name,guesses=0)
            return game.to_form(' Game over!')

        # check if game is over
        if game.game_over:
            return game.to_form('Game already over!')
        # reduce the remaining_attempts by one to keep track of number of moves left
        game.attempts_remaining -= 1
        userGuess = request.guess.upper()
        
        # check if user guessed the complete word
        if userGuess == game.target:
            score = Score(won=True,guesses=game.attempts_remaining,
                        user=game.user_name,key=s_key)
            score.put()
            game.end_game(won=True,user_name=game.user_name,
                          guesses=game.attempts_allowed - game.attempts_remaining)
            # store game entry for game history
            game.store_move(guess=userGuess, message='you win',game=game)
            # update guessed word
            game.guess = userGuess
            game.put()
            return game.to_form('You win!')        
        
        # check if user has entered more than one alphabet but not the whole word
        if len(userGuess) > 1:
            game.store_move(guess=userGuess, message='Invalid entry',game=game)
            retStr = 'You can enter more than one alphabet only if you know the complete word'
            return game.to_form(retStr)

        wordLst = list (game.target)
        wordFlag = False
        word = list(game.guess)
        
        # check user entry for any correct guesses
        for idx,val in enumerate(wordLst):
          if val == userGuess:
            wordFlag = True
            word[idx] = val
        #if correct guess
        if(wordFlag):
          game.guess = "".join(word)
          game.put()
          # check if game is compleated
          if game.guess == game.target:
            game.end_game(won=True,user_name=game.user_name,
                          guesses=game.attempts_allowed - game.attempts_remaining)
            score = Score(won=True,guesses=game.attempts_remaining,
                        user=game.user_name,key=s_key)
            score.put()
            game.store_move(guess=userGuess, message='you win',game=game)
            return game.to_form('You win!')        
          else: 
            game.store_move(guess=userGuess, message='correct guess',game=game)
            return game.to_form('right guess')
        else:
          game.store_move(guess=userGuess, message="you're wrong",game=game)
          # provide hint message 
          if(game.attempts_remaining == 5 or game.attempts_remaining == 6):
            retStr = " HINT : seems like you need help the first 3 charecters are "
            return game.to_form(retStr+wordLst[0]+wordLst[1]+wordLst[2])
          return game.to_form("Nope , You're wrong")


    ''' 
     Get all user games that have not finished 
     name : get_user_games
     returns  
     json dumps of an array of all unfinished games info 
    '''
    @endpoints.method(name="get_user_games",request_message=get_user_name, 
                      response_message=USER_GAMES,http_method = "GET")
    def get_user_games(self,request):
        """Get unfinished games of a user"""
        user_name = request.user_name
        # query games for the user
        q = Game.query(ancestor = ndb.Key(User,user_name))
        q.fetch()
        arr = []
        for i in q:
           if i.game_over == False:
             arr.append(json.dumps({'progress':i.guess,
                        'attempts_remaining':i.attempts_remaining,
                        'game_over':i.game_over}))
        return USER_GAMES(response=arr)

    ''' 
     cancel(delete) all unfinished games of a user 
     name : cancel_games
     returns  
     message : confermation of game deletions 
    '''
    @endpoints.method(name="cancel_games",request_message=CANCEL_GAME, 
                      response_message=DELETE_GAMES,http_method = "DELETE")
    def cancel_games(self,request):
        """Delete a users game"""
        url_safe = request.urlsafe_game_key
        try:
          game = get_by_urlsafe(request.urlsafe_game_key, Game)
          if(game.game_over == False):
            game.key.delete()
            return DELETE_GAMES(response='Specified game deleted')
          else:
            return DELETE_GAMES(response='This game is over, Delete not possible')
        except Exception as e:
          return DELETE_GAMES(response='Specified game does not exist')

    ''' 
     get users with high scores   
     name : high_scores
     returns  
     json dumps : list of tuples ('username','score') 
    '''
    @endpoints.method(name="high_scores",request_message=set_limit,
                      http_method="GET",response_message=high_score)
    def high_scores(self,request):
      """Get games with high score"""
      q = Score.query()
      if(request.limit):
        res = q.order(-Score.guesses).fetch(request.limit)
        # query scores in decending order
      else:
        res = q.order(-Score.guesses)
      arr = []
      for i in res:
       arr.append( (i.user, i.guesses) )
      return high_score(response=str(arr) ) 

    ''' 
     Get the ranking table (decided by win percentage of user) 
     name : ranking_table
     returns  
     json dumps : list of tuples ('username','win_percent')
    '''
    @endpoints.method(name="ranking_table",request_message=set_limit,
                      http_method="GET",response_message=high_score)
    def ranking_table(self,request):
       """Get player rankings"""
       q = User.query()
       if (request.limit):
         res = q.order(-User.win_percent).fetch(request.limit)
       else:
         res = q.order(-User.win_percent)
       arr = []
       for i in res:
        if(i.win_percent != 0):
          arr.append( (i.name, i.win_percent) )
       return high_score(response=str(arr) ) 

    ''' 
     get history (moves made) for a game 
     name : get_game_history
     returns  
     json dumps : list of tuples ('move_made','response msg') 
    '''
    @endpoints.method(http_method="GET",name="get_game_history",
                    request_message=GET_HISTORY,response_message=StringMessage)
    def get_game_history(self,request):
       """Get history of all moves played in a game"""
       game = get_by_urlsafe(request.urlsafe_game_key, Game)
       return StringMessage(message=game.history )



api = endpoints.api_server([hangman])