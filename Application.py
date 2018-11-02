# $ export FLASK_APP=Application.py
# $ python -m flask run


import os
import datetime
import pytz
import sqlite3 as lite

from datetime               import datetime, tzinfo, timedelta
from flask                  import Flask, flash, redirect, render_template, request, session
from flask_session          import Session
from tempfile               import mkdtemp
from werkzeug.exceptions    import default_exceptions
from werkzeug.security      import check_password_hash, generate_password_hash


from helper import falseHash, dehash



app = Flask("tracker")
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# Set up database connection
con = None




@app.route("/")
def main():
    # TODO: make it so that if you aren't logged in, you're automatically brought to login page?

    # You are currently in the following games:
    # Table of games
    # Button on the far right of the table that says 'Manage'. Clicking it takes you to that game's page
    # Button at the bottom that says 'Create a new game' that takes you to the create game page, the same way that clicking on the header does.
    if session.get("user_id") is None:
        return render_template("welcome.html")
    else:
        con = lite.connect("finalproject.db")
        with con:
            cur = con.cursor()
            cur.execute("SELECT rpgID FROM players WHERE usersID = ?", [session["user_id"][0]])
            gameIDs   = cur.fetchall()
        if gameIDs != []:
            ids = []
            for id in gameIDs:
                ids.append(id[0])
            
            with con:
                cur = con.cursor()
                print(str(ids))
                idlist = str(ids)[1:-1]
                
                print(idlist)
                print(session["user_id"][0])
                # cur.execute("SELECT * FROM rpgs WHERE id in (?) AND NOT GMid = ?", [idlist, session["user_id"][0]])
                cur.execute("SELECT * FROM rpgs WHERE id in (8, 9, 10, 11, 13) AND NOT GMid = 5")
                gamesPlayingList = cur.fetchall()
                print(gamesPlayingList)
                cur.execute("SELECT * FROM rpgs WHERE id in (?) AND GMid = ?", [idlist, session["user_id"][0]])
                gamesGMing = cur.fetchall()
                print(gamesGMing)
        else:
            gamesPlayingList = []
            gamesGMing = []

        con.close()
        return render_template("main.html", gamesPlayingList = gamesPlayingList, gamesGMing = gamesGMing)




@app.route("/login", methods = ["POST", "GET"])
def login():
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            flash('You need to include a username')
            return render_template("login.html")

        # Ensure password was submitted
        elif not request.form.get("password"):
           flash('You need to include a password')
           return render_template("login.html")

        # Query database for username
        con = lite.connect("finalproject.db")
        with con:
            cur = con.cursor()
            cur.execute("SELECT passwordhash FROM users WHERE username = ?",
                               [request.form.get("username")])
            rows = cur.fetchone()

        # Ensure username exists and password is correct

        if rows == None or (check_password_hash(rows[0], request.form.get("password")) == False):
            flash('Invalid username or password')
            print("\n"+str(rows != None)+"\n")
            print("\n"+str(check_password_hash(rows[0], request.form.get("password")))+"\n")
            return render_template("login.html")

        # Remember which user has logged in
        with con:
            cur = con.cursor()
            cur.execute("SELECT id FROM users WHERE username = ?",
                               [request.form.get("username")])
            rows = cur.fetchone()
        session["user_id"] = rows

        # Redirect user to home page
        if (session.get("followUp") is None):
            con.close()
            return redirect("/")
        else:
            destination = session.get("followUp")
            session["followUp"] = None
            con.close()
            return redirect(destination)

    else:
        return render_template("login.html")

@app.route("/register", methods = ["POST", "GET"])
def register():
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            flash("Please provide a username")
            return render_template("register.html")
        # Ensure password was submitted
        elif not request.form.get("password"):
            flash("Please provide a password")
            return render_template("register.html")

        if request.form.get("password") != request.form.get("password2"):
            flash("Those passwords don't match")
            return render_template("register.html")


        username = request.form.get("username")
        password = request.form.get("password")
        # Query database for username to make sure that user doesn't already exist
        con = lite.connect("finalproject.db")
        with con:
            cur = con.cursor()
            cur.execute("SELECT * FROM users WHERE username = ?", [username])
            thisrows = cur.fetchone()
        if thisrows != None:
            flash("Someone with that username already exists. Did you forget your password?")
            return render_template("register.html")
        else:
        #If all that's good to go, create the user, then redirect
            userspassword = generate_password_hash(request.form.get("password"))
            with con:
                cur = con.cursor()
                cur.execute("INSERT INTO users (username, passwordhash, email) VALUES (?, ?, ?)", 
                    [request.form.get("username"), userspassword, request.form.get("email")])
                cur.execute("SELECT * FROM users WHERE username = ?", [request.form.get("username")])
                thisrows = cur.fetchone()
                print(thisrows[0])
                session["user_id"] = thisrows[0]

        #redirect user to the proper next page and close the connection
        if (session.get("followUp") is None):
            if con:
                con.close()
            return redirect("/")
        else:
            if con:
                con.close()
            destination = session.get["followUp"]
            session["followUp"] = None
            return redirect(destination)

    else:
        return render_template("register.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/create", methods = ["POST", "GET"])
def create():
    if request.method == "POST":
        if not request.form.get("RPGName"):
            flash("Please provide a name for your RPG")
            return render_template("create.html")
        if not request.form.get("Description"):
            flash("Please provide a description for your RPG")
            return render_template("create.html")

        thisrpgName = request.form.get("RPGName")
        rows = db.execute("SELECT * FROM rpgs WHERE name = :RPGName", RPGName = thisrpgName)
        if len(rows) == 1:
            flash("An RPG with that name already exists. Please input a different name.")
            return render_template("create.html")
        else:
            db.execute("INSERT INTO rpgs (GMid, name, description) VALUES (:GMid, :name, :description)",
                GMid = session.get("user_id"), name = thisrpgName, description = request.form.get("Description"))

            rows2 = db.execute("SELECT id FROM rpgs WHERE name = :newRPGNAME", newRPGNAME = thisrpgName)
            thisRPGid = rows2[0]["id"]
            db.execute("INSERT INTO players (rpgID, usersID) VALUES (:rpgID, :userID)",
                rpgID = thisRPGid, userID = session.get("user_id"))
            return redirect("/")
    else:
        return render_template("create.html")


@app.route("/settings", methods = ["POST", "GET"])
def settings():
    if request.method == "POST":
        if request.form.get("username"):
            newUsername = request.form.get("username")
            db.execute("UPDATE users SET username = :newusername WHERE id = :user", newusername = newUsername, user = session.get("user_id"))
            session.get("user_id") == newUsername
        if request.form.get("timezone"):
            try:
                newTimezone = int(request.form.get("timezone"))
            except:
                flash("You have input something that is not a number. Please try again.")
                rows = db.execute("SELECT * FROM users WHERE id = :user", user = session.get("user_id"))
                return render_template("settings.html", username = rows[0]["username"], timezone = rows[0]["timezone"])
            if newTimezone > 13 or newTimezone < -11:
                flash("You have input an invalid timezone. Please try again.")
                rows = db.execute("SELECT * FROM users WHERE id = :user", user = session.get("user_id"))
                return render_template("settings.html", username = rows[0]["username"], timezone = rows[0]["timezone"])
            else:
                rows = db.execute("UPDATE users SET timezone = :newTimeZone WHERE id = :user", newTimeZone = newTimezone, user = session.get("user_id"))
        rows = db.execute("SELECT * FROM users WHERE id = :user", user = session.get("user_id"))
        return render_template("settings.html", username = rows[0]["username"], timezone = rows[0]["timezone"] )
    else:
        rows = db.execute("SELECT * FROM users WHERE id = :user", user = session.get("user_id"))
        return render_template("settings.html", username = rows[0]["username"], timezone = rows[0]["timezone"])

@app.route("/rpg")
def rpg():
    thisID = request.args.get('rpgID')
    rows = db.execute("SELECT * FROM rpgs WHERE id = :rpgID", rpgID = thisID)

    gameName = rows[0]["Name"]
    gameDescription = rows[0]["Description"]
    gameID = rows[0]["id"]

    gameGMID = rows[0]["GMid"]
    gmrows = db.execute("SELECT * FROM users WHERE id = :gmID", gmID = gameGMID)
    thisGMName = gmrows[0]["username"]

    playerIDs = db.execute("SELECT * FROM players WHERE rpgID = :thisID", thisID = gameID)
    if playerIDs != []:
        ids = []
        for id in playerIDs:
            ids.append(id.get("usersID"))
        thisplayerlist = db.execute("SELECT * FROM users WHERE id in (:idlist)", idlist = ids)
    else:
        thisplayerlist = []

    thisHash = falseHash(gameID)
    if gameGMID == session.get("user_id"):
        thisisGM = True
        thisisPlayer = False
    else:
        thisisGM = False
        rows2 = db.execute("SELECT * FROM players WHERE rpgID = :thisID AND usersID = :thisUser" , thisID = gameID, thisUser = session.get("user_id"))
        if len(rows2) == 1:
            thisisPlayer = True
        else:
            thisisPlayer = False
    currentTime = datetime.now()
    print(currentTime)
    try:
        rows3 = db.execute("SELECT * FROM users WHERE id = :thisUser", thisUser = session.get("user_id"))
    except:
        flash("Please log in")
        return redirect("/")
    thisTimeZone = rows3[0]["timezone"]
    currentTime = currentTime + timedelta(hours=int(thisTimeZone))
    print(currentTime)
    try:
        scheduleRows = db.execute("SELECT * FROM rpgmeetings WHERE rpgID = :thisID AND MeetingTime > :currentTime ORDER BY MeetingTime ASC",
            thisID = gameID, currentTime = str(currentTime))
        print(scheduleRows)
        i = 0
        meetingsList = []
        while i < len(scheduleRows):
            meeting = datetime.strptime(scheduleRows[i]["MeetingTime"], '%Y-%m-%d %H:%M:%S') + timedelta(hours=int(thisTimeZone)) - timedelta(hours=int(scheduleRows[i]["timezone"]))
            meeting = meeting.strftime("%I:%M%p %A, %b %d, %Y")
            meetingsList.append(meeting)
            i += 1
        nextMeeting = meetingsList[0]
        thisTimezone = "(UTC "+str(thisTimeZone)+" hours)"
    except:
        nextMeeting = "No meeting currently scheduled"
        thisTimezone = ""


    return render_template("rpg.html", rpgname = gameName, rpgDescription = gameDescription, gmName = thisGMName,
        rpgID = gameID, playerlist = thisplayerlist, inviteHash = thisHash, isGM = thisisGM, isPlayer = thisisPlayer,
        nextMeeting = nextMeeting, meetingsList = meetingsList, timezone = thisTimezone)

@app.route("/dropPlayer", methods = ["POST", "GET"])
def dropPlayer():
    if request.method == "POST":
        thisgameID = request.form.get("rpgID")
        thisplayerID = request.form.get("playerID")
        if thisgameID is None:
            flash("Invalid ID")
            return redirect("/")
        rows = db.execute("SELECT * FROM rpgs WHERE id = :rpgID", rpgID = thisgameID)
        if (rows[0]["GMid"] != session.get("user_id")):
            flash("You cannot remove players from games that you aren't GMing")
            return redirect("/")
        else:
            db.execute("DELETE FROM players WHERE rpgID = :rpgID AND usersID = :thisPlayer", rpgID = thisgameID, thisPlayer = thisplayerID)
            return redirect("rpg?rpgID="+thisgameID)
    else:
        thisID = request.args.get('rpgID')
        thisPlayer = request.args.get('playerID')
        rows = db.execute("SELECT * FROM users WHERE id = :playerID", playerID = thisPlayer)
        thisplayerName = rows[0]["username"]
        rows = db.execute("SELECT * FROM rpgs WHERE id = :rpgID", rpgID = thisID)
        thisRPGName = rows[0]["Name"]
        return render_template("dropPlayer.html", rpgID = thisID, playerID = thisPlayer, playerName = thisplayerName, RPGName = thisRPGName)

@app.route("/rpgedit", methods = ["POST", "GET"])
def rpgedit():
    if request.method == "POST":
        if not request.form.get("rpgID"):
            flash("You shouldn't be here")
            return redirect("/")
        if not request.form.get("gameName"):
            flash("Please provide a name for your RPG")
            return redirect("/")
        if not request.form.get("gameDescription"):
            flash("Please provide a description for your RPG")
            return redirect("/")

        rpgID = request.form.get("rpgID")
        newgameDescription = request.form.get("gameDescription")
        newgameName = request.form.get("gameName")




        db.execute("UPDATE rpgs SET name = :gameName, description = :gameDescription WHERE id = :rpgID",
            gameName = request.form.get("gameName"), gameDescription = request.form.get("gameDescription"), rpgID = request.form.get("rpgID"))

        return redirect("/")
    else:
        thisID = request.args.get('rpgID')
        rows = db.execute("SELECT * FROM rpgs WHERE id = :rpgID", rpgID = thisID)
        if (rows[0]["GMid"] != session.get("user_id")):
            flash("You cannot edit RPGs that you are not the GM for")
            return redirect("/")

        gameName = rows[0]["Name"]
        gameDescription = rows[0]["Description"]
        gameID = rows[0]["id"]

        gameGMID = rows[0]["GMid"]
        gmrows = db.execute("SELECT * FROM users WHERE id = :gmID", gmID = gameGMID)
        thisGMName = gmrows[0]["username"]

        playerIDs = db.execute("SELECT * FROM players WHERE rpgID = :thisID", thisID = gameID)
        if playerIDs != []:
            ids = []
            for id in playerIDs:
                ids.append(id.get("usersID"))
            thisplayerlist = db.execute("SELECT * FROM users WHERE id in (:idlist)", idlist = ids)
        else:
            thisplayerlist = []
        return render_template("rpgedit.html", rpgname = gameName, rpgDescription = gameDescription, gmName = thisGMName, playerlist = thisplayerlist, rpgID = gameID)

@app.route("/deleterpg", methods = ["GET", "POST"])
def deleterpg():
    if request.method == "POST":
        gameID = request.form.get("rpgID")
        db.execute("DELETE FROM rpgs WHERE id = :rpgID", rpgID = gameID)
        db.execute("DELETE FROM players WHERE rpgID = :rpgID", rpgID = gameID)
        return redirect("/")
    else:
        gameID = request.args.get('rpgID')
        rows = db.execute("SELECT * FROM rpgs WHERE id = :rpgID", rpgID = gameID)
        if (rows[0]["GMid"] != session.get("user_id")):
            flash("You cannot delete RPGs that you are not the GM for")
            return redirect("/")
        return render_template("deleterpg.html", RPGName = rows[0]["Name"], rpgID = rows[0]["id"])

@app.route("/invite", methods = ["GET", "POST"])
def invite():
    if request.method == "POST":
        if session.get("user_id") is None:
            flash("Must login or register before joining this RPG.")
            session["followUp"] = "/invite?code="+str(request.form.get("gameHash"))
            return redirect("/login")
        else:
            gameID = int(dehash(request.form.get("gameHash")))
            rows = db.execute("SELECT * FROM players WHERE rpgID = :thisGame AND usersID = :thisUser", thisGame = gameID, thisUser = session.get("user_id"))
            if len(rows) == 0:
                db.execute("INSERT INTO players (rpgID, usersID) VALUES (:thisGame, :thisUser)", thisGame = gameID, thisUser = session.get("user_id"))
                destination = "/rpg?rpgID="+str(gameID)
                flash("You've joined this RPG!")
                return redirect(destination)
            else:
                destination = "/rpg?rpgID="+str(gameID)
                flash("You cannot join this RPG because you are already in this RPG")
                return redirect(destination)
    else:
        thisgameHash = request.args.get('code')
        gameID = int(dehash(thisgameHash))
        rows = db.execute("SELECT * FROM rpgs WHERE id = :rpgID", rpgID = gameID)
        return render_template("invite.html", RPGName = rows[0]["Name"], Description = rows[0]["Description"], gameHash = thisgameHash)

@app.route("/schedule", methods = ["POST", "GET"])
def schedule():
    if request.method == "POST":
        if request.form['action'] == 'Submit':
            thisID = request.form.get("gameID")
            dateAttempt = request.form.get("date")
            timeAttempt = request.form.get("time")
            locationAttempt = request.form.get("location")
            if not request.form.get("date"):
                flash("You must input a valid date in DD/MM/YYYY format")
                return render_template("schedule.html", gameID = thisID,
                    dateAttempt = dateAttempt, timeAttempt = timeAttempt, locationAttempt = locationAttempt)
            if not request.form.get("time"):
                flash("You must input a valid time in MM:HH military time")
                return render_template("schedule.html", gameID = thisID,
                    dateAttempt = dateAttempt, timeAttempt = timeAttempt, locationAttempt = locationAttempt)
            if not request.form.get("location"):
                flash("You must give a valid location")
                return render_template("schedule.html", gameID = thisID,
                    dateAttempt = dateAttempt, timeAttempt = timeAttempt, locationAttempt = locationAttempt)
            date = str(request.form.get("date"))
            time = str(request.form.get("time"))
            combined = date + " " + time
            try:
                meetingDateTime = datetime.strptime(combined, '%m/%d/%Y %H:%M')
            except:
                flash("You didn't give date or time in a valid format. Please try again.")
                return render_template("schedule.html", gameID = thisID,
                    dateAttempt = dateAttempt, timeAttempt = timeAttempt, locationAttempt = locationAttempt)

            db.execute("INSERT INTO rpgMeetings (Location, MeetingTime, rpgID, timezone) VALUES (:thisLocation, :thisTime, :thisRPG, :thisTimezone)",
                thisLocation = locationAttempt, thisTime = str(meetingDateTime), thisRPG = thisID, thisTimezone = request.form.get("timezone"))
            flash("Meeting added")
            return redirect("rpg?rpgID="+thisID)
        elif request.form['action'] == 'Check':
            thisID = request.form.get("gameID")
            dateAttempt = request.form.get("date")
            timeAttempt = request.form.get("time")
            locationAttempt = request.form.get("location")
            if not request.form.get("date"):
                flash("You must input a valid date in DD/MM/YYYY format")
                return render_template("schedule.html", gameID = thisID,
                    dateAttempt = dateAttempt, timeAttempt = timeAttempt, locationAttempt = locationAttempt)
            if not request.form.get("time"):
                flash("You must input a valid time in MM:HH military time")
                return render_template("schedule.html", gameID = thisID,
                    dateAttempt = dateAttempt, timeAttempt = timeAttempt, locationAttempt = locationAttempt)
            if not request.form.get("location"):
                flash("You must give a valid location")
                return render_template("schedule.html", gameID = thisID,
                    dateAttempt = dateAttempt, timeAttempt = timeAttempt, locationAttempt = locationAttempt)
            date = str(request.form.get("date"))
            time = str(request.form.get("time"))
            combined = date + " " + time
            GMTime = db.execute("SELECT * FROM users WHERE id = :userID", userID = session["user_id"])
            try:
                meetingDateTime = datetime.strptime(combined, '%m/%d/%Y %H:%M') - timedelta(hours=int(GMTime[0]["timezone"]))
            except:
                flash("You didn't give date or time in a valid format. Please try again.")
                return render_template("schedule.html", gameID = thisID,
                    dateAttempt = dateAttempt, timeAttempt = timeAttempt, locationAttempt = locationAttempt)

            print(str(meetingDateTime))
            rows = db.execute("SELECT usersID FROM players WHERE rpgID = :gameID", gameID = thisID)
            ids = []
            if rows != []:
                for id in rows:
                    if id.get("usersID") != session["user_id"]:
                        ids.append(id.get("usersID"))
            rows2 = db.execute("SELECT * FROM users WHERE id in (:idlist)", idlist = ids)
            # print(rows2)
            playerTimes = []
            for user in rows2:
                thisPlayerTime = meetingDateTime + timedelta(hours=int(user.get("timezone")))
                thisPlayerTime = thisPlayerTime.strftime("%I:%M%p %A, %b %d, %Y")
                playerTimes.append(user.get("username")+": " + str(thisPlayerTime))

            return render_template("schedule.html", gameID = thisID,
                    dateAttempt = dateAttempt, timeAttempt = timeAttempt, locationAttempt = locationAttempt, playerTimes = playerTimes)
    else:
        thisID = request.args.get('rpgID')
        if thisID is None:
            flash("Invalid ID")
            return redirect("/")
        rows = db.execute("SELECT * FROM rpgs WHERE id = :rpgID", rpgID = thisID)
        if (rows[0]["GMid"] != session.get("user_id")):
            flash("You cannot edit RPGs that you are not the GM for")
            return redirect("/")
        rows = db.execute("SELECT * FROM users WHERE id = :userID", userID = session.get("user_id"))
        return render_template("schedule.html", gameID = thisID, timezone = rows[0]["timezone"])

@app.route("/leaveRPG", methods = ["POST", "GET"])
def leaveRPG():
    if request.method == "POST":
        thisID = request.form.get("rpgID")
        if thisID is None:
            flash("Invalid ID")
            return redirect("/")
        rows = db.execute("SELECT * FROM players WHERE id = :rpgID AND usersID = :thisUser", rpgID = thisID, thisUser = session.get("user_id"))
        if len(rows) != 1:
            flash("You are not in this RPG")
        else:
            db.execute("DELETE FROM players WHERE id = :rpgID AND usersID = :thisUser", rpgID = thisID, thisUser = session.get("user_id"))
        return redirect("/")
    else:
        thisID = request.args.get('rpgID')
        return render_template("leaveRPG.html", rpgID = thisID)