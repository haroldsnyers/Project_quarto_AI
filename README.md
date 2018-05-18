Seynaeve Alexandre 16169

Snyers Harold 16243
___
# Project_quarto_AI
For the final project in second bachelor at the ECAM (industrial engineering) who are oriented in electrical engineering, the students were asked for the cours informatics ADVANCED PYTHON, to create an artificial intelligence able to play the game Quarto. To do this, we were given a code with the structure of the game, State and Server, and a library [game.py](https://github.com/ECAM-Brussels/PythonAdvanced2BA/tree/master/AIproject/lib). 

## How does it works
To create our artificial intelligence, we had the idea to dissociate it in two parts. Firstly by making it play very much alike a human and secondly after a few moves made by the human part, by calling upon the library [EasyAI](http://zulko.github.io/easyAI/index.html). From this library we used different algorithms like Negamax, SSS and solving. 

The human part generates moves according to some rules/instructions we gave him. This part of the AI is interesting because it gives a certain variety to each game. It chooses moves, randomly from a targeted list, which could be interesting for the future of the game. 

The part of our intelligence which calls upon the EasyAI uses different methods, firstly it uses the method AI_Player 3 times with different depths (we change the depths to reduce the time the AI uses to think for a move). One of the AI_player uses SSS, the other one uses Negamax. These two AI_Player will play against each other from the state of the game and will finally return the best move out of the games they did. For the last moves, we use the method id_solving from the class solving which returns the most interesting move in order to win.

We think by making our Artificial Intelligence think like a human and like a machine, makes him more difficult to play against.

#### What do you need to launch a game
To start a new game you will have to open 3 command prompts or terminals and call the game from the dossier where quarto_AI.py is saved.
  1. [window 1] : the server from the game
  2. [window 2] : Client 1 from the game
  3. [window 3] : Client 2 from the game

*you can launch 2 times the same client or launch a client from another dossier which uses the same game structure and server*

#### The different intelligences
  1. **AI** : the actual intelligence
  2. **BOT1** : AI to test main AI *(lvl1)   (human + id_solve(2,4))*
  3. **BOT2** : AI to test main AI *(lvl4)   (human + Negamax(6), SSS(3))*
  4. **BOT3** : AI to test main AI *(lvl2)   (id_solve(2,4))*
  5. **BOT4** : AI to test main AI *(lvl3)   (Negamax(6), SSS(3))*
  6. **player** : to play against the AI or between 2 players

#### How to launch a game
##### Server
```html
python quarto_AI.py server --verbose
```
##### Client
```html
python quarto_AI.py <Intelligence> <Name> --verbose
```
##### Server from abroad
```html
python quarto_AI.py server --verbose --host=<IP> --port=<Port>
```
##### Client from abroad

```html
python quarto_AI.py <Intelligence> <Nom> --verbose --host=<IP> --port=<Port>
```    
