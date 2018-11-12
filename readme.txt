Hello. This is the flask adventure tracker.

If you are interested in running this locally, download it then CD into the directory it is in. Execute the two commands located at the top of Application.py, reposted here for clarity:
--export FLASK_APP=Application.py
--python -m flask run

The database is currently titled "finalproject.db" as this was my final for Harvard's cs50 class. Changing it shouldn't alter any functionality as long as you replace all the references.

There are several users in the database currently, all of which have the password "test". They're signed up for each other's games and running their own ones. Feel free to log in, leave games, join new ones, create new ones, or mess with settings. 


Joining RPGs:
All of your RPGs have an invite link associated with them. If you click on it, it'll take you to a page asking if you want to join the game. Copy the URL, and send it to anyone who you want to join. If a player who is already in a game attempts to join it, nothing happens. You can drop any players who you want out of your game.