Seynaeve Alexandre 16169

Snyers Harold 16243
___
# Project_quarto_AI
This is the final project asked for the students in second bachelor at the ECAM (industrial engineering) who are oriented in electrical engineering, for informatics ADVANCED PYTHON.
We were asked to create an artificial intelligence able to play the game Quarto. To do this we were given a code with the structure of the game and a library which is used for the structure. 

## How does it works
To create our artificial intelligence, we had the idea to dissociate it in two parts. Firstly by making it play very much alike a human and secondly after a few moves made by the human part by calling upon the library EasyAI. From this library we used different algorithms like Negamax, mtd and solving which uses negamax with different depths. 

The human part generates moves according to some rules we gave him. This part of the AI is interesting because it gives a certain variety to each game. It chooses moves, randomly from a targeted list, which could be interesting for the future of the game without necessarily being a guaranteed victory.

The part of our intelligence which calls upon the EasyAI uses the method id_solving from the class solving which returns the most interesting move in order to win.

#### What do you need to launch a game
To start a game you will have to open 3 command prompts or terminals and call the game from the dossier where it is saved.
  1. [window 1] : the server from the game
  2. [window 2] : Client 1 from the game
  3. [window 3] : CLient 2 from the game

*you can launch 2 times the same client or launch a client from another dossier which uses the same game structure and server*

#### The different intelligences
  1. AI : the actual intelligence
  2. player : to play against the AI or between 2 players

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
