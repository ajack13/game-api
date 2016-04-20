# Game API 
API with endpoints that will allow anyone to develop a front-end for a game.
The project has code for the classic game hangman but can be extended to create lots of fun games 

###  The Hangman Game
The classic game hangman gives you 10 chances to guess a word, one alphabet at a time if you can guess the word before you attempts run out then you win the game

The game will give you a hint if you have'nt guessed the word correctly at the 5th attempt

Response are in the form of a string so they can be reconstructed to json in the client

### Up and running with the game api
Download google app engine for your operating system and register you app in the google developer console

### Required Libraries and dependencies
1) Git (optional)

2) A gmail id , google app engine
### Installation

download zip    

Unzip the file 
```sh
$ cd game-api
```
or
    
Clone github repository
    
Open the shell in mac/linux or command prompt in windows and navigate to the folder you wnat to clone the repository
    
Make sure you have installed git
    
```sh
    $ git clone https://github.com/ajack13/game-api.git
```
this should clone the repository to the folder

Add the code as an existing project in app engine and change the project key

Create a `User` or two , Create a game (api : new_game) and play a few games.
Make sure to take a look at the admin Datastore viewer to check out the various entities.
The datastore is typically at http://localhost:8000, but you may need to access it on another port based on what port your app engine has assigned to the app.

## Files Included:
 - api.py: Contains endpoints and game playing logic.
 - app.yaml: App configuration.
 - cron.yaml: Cronjob configuration.
 - main.py: Handler for taskqueue handler.
 - models.py: Entity and message definitions including helper methods.
 - utils.py: Helper function for retrieving ndb.Models by urlsafe Key string.

## Models Included:
 - **User**
    - Stores unique user_name and (optional) email address.
    
 - **Game**
    - Stores unique game states. Associated with User model via KeyProperty.
    
 - **Score**
    - Records completed games. Associated with Users model via KeyProperty.

### API's
 - **get_user_games**
    - args : user_name
    - type : GET
    - This returns all of a User's active games. 
    - Each game is a `descendant` of a `User`.
    - the response is given as json dumps (string)
    
 - **cancel_game**
    - args : user_name
    - type : POST
    - This endpoint allows users to cancel a game in progress.
    - Deleting the Game model for unfinished games
    - response is a succes message(string) 
    
 - **get_high_scores**
    - args : none
    - type : GET
   - Generate a list of high scores in descending order, a leader-board!
    - Accepts an optional parameter `number_of_results` that limits the number of results returned.
    - returns a list of tuples ,users and their score
    
 - **get_user_rankings**
    - args : none
    - type : GET
    - Ranking the performance of each player based on number of wins.
    - ranked based on win percentage
    - returns a list of tuples , users and their win percentage
 
 - **get_game_history**
    - type : GET
    - args : none
    - This returns the history of moves the player made and the response for each move.
    - each and every move is stored in the Game model
    - response is a list of tuples , (move_made,response)

### Notifications
  - A cron job and associated handler have been created (see cron.yaml and main.py).
This sends an hourly reminder email to Users with unfinished games an email 

