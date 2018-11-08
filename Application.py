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
    # You are currently in the following games:
    # Table of games
    # Button on the far right of the table that says 'Manage'. Clicking it takes you to that game's page
    if session.get("user_id") is None:
        return render_template("welcome.html")
    else:
        con = lite.connect("finalproject.db")
        with con:
            cur = con.cursor()
            cur.execute("SELECT rpgID FROM players WHERE usersID = ?", [session["user_id"][0]])
            gameIDs   = cur.fetchall()
        if gameIDs != []:
            #iterate through all the games that the user is a player/GM in
            ids = []
            for id in gameIDs:
                ids.append(id[0])
            
            with con:
                cur = con.cursor()
                idlist = str(ids)[1:-1]
                
                #fetch all the games that user is a player in, and save that to one variable. 
                cur.execute("SELECT * FROM rpgs WHERE id in ({0}) AND NOT GMid = {1}".format(idlist, session["user_id"][0]))
                gamesPlayingList = cur.fetchall()
                #fetch all the games where the user is a GM, save that to another variable.
                cur.execute("SELECT * FROM rpgs WHERE id in ({0}) AND GMid = {1}".format(idlist, session["user_id"][0]))
                gamesGMing = cur.fetchall()
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
        con = lite.connect("finalproject.db")
        cur = con.cursor()

        cur.execute("SELECT * FROM rpgs WHERE name = ?", [thisrpgName])
        rows = cur.fetchone()
        #We first check to see if there is already an RPG with that name, if so the user must choose a new RPG name
        if rows != None:
            flash("An RPG with that name already exists. Please input a different name.")
            con.close()
            return render_template("create.html")
        else:
            thisuser = session.get("user_id")
            thisuser = str(thisuser)[1:-2]
            thisdescription = request.form.get("Description")
            #Then, we create the RPG and add the user to it as the first "player" (even though they're a GM)
            cur.execute("INSERT INTO rpgs (GMid, name, description) VALUES (?, ?, ?)",
                [thisuser, thisrpgName, thisdescription])

            cur.execute("SELECT id FROM rpgs WHERE name = ?", [thisrpgName])
            rows2 = cur.fetchone()
            thisRPGid = rows2[0]
            print(thisRPGid)
            cur.execute("INSERT INTO players (rpgID, usersID) VALUES (?, ?)",
                [thisRPGid, thisuser])
            
            con.close()
            return redirect("/")
    else:
        return render_template("create.html")


@app.route("/settings", methods = ["POST", "GET"])
def settings():
    con = lite.connect("finalproject.db")
    cur = con.cursor()
    if request.method == "POST":
        thisuser = session.get("user_id")
        thisuser = str(thisuser)[1:-2]
        if request.form.get("username"):
            #usernames are unique, so we need to make sure no one else in the database has that username. 
            #If someone does, we flash an alert.
            newUsername = request.form.get("username")
            cur.execute("SELECT id FROM users WHERE username = ?", [newUsername])
            rows = cur.fetchone()
            if rows == None:
                cur.execute("UPDATE users SET username = ? WHERE id = ?", [newUsername, thisuser])
            else:
                flash("Someone already has that username! Please try again.")
        if request.form.get("timezone"):
            #Now we're gonna set a new timezone. Throughout this process, if the input isn't valid, then they are returned
            #the same template, automatically filled in with their default settings
            #Try//except block is a good way of catching problematic inputs.
            try:
                newTimezone = int(request.form.get("timezone"))
            except:
                flash("You have input something that is not a number. Please try again.")
                cur.execute("SELECT * FROM users WHERE id = ?", [thisuser])
                rows = cur.fetchone()
                return render_template("settings.html", username = rows[1], timezone = rows[5])
            if newTimezone > 13 or newTimezone < -11:
                flash("You have input an invalid timezone. Please try again.")
                cur.execute("SELECT * FROM users WHERE id = ?", [thisuser])
                rows = cur.fetchone()
                return render_template("settings.html", username = rows[1], timezone = rows[5])
            else:
                cur.execute("UPDATE users SET timezone = ? WHERE id = ?", [newTimezone, thisuser])
        #now rerender the template with their default settings (potentially now changed)
        cur.execute("SELECT * FROM users WHERE id = ?", [thisuser])
        rows = cur.fetchone()
        con.close()
        return render_template("settings.html", username = rows[1], timezone = rows[5] )
    else:
        thisuser = session.get("user_id")
        thisuser = str(thisuser)[1:-2]
        cur.execute("SELECT * FROM users WHERE id = ?", [thisuser])
        rows = cur.fetchone()
        con.close()
        return render_template("settings.html", username = rows[1], timezone = rows[5])

@app.route("/rpg")
def rpg():
    con = lite.connect("finalproject.db")
    cur = con.cursor()

    thisID = request.args.get('rpgID')
    cur.execute("SELECT * FROM rpgs WHERE id = ?", [thisID])
    rows = cur.fetchone()

    gameName = rows[2]
    gameDescription = rows[3]
    gameID = rows[0]

    gameGMID = rows[1]
    cur.execute("SELECT * FROM users WHERE id = ?", [gameGMID])
    gmrows = cur.fetchone()
    thisGMName = gmrows[1]

    cur.execute("SELECT * FROM players WHERE rpgID = ?", [gameID])
    playerIDs = cur.fetchall()
    if playerIDs != []:
        ids = []
        for id in playerIDs:
            ids.append(id[0])

        idlists = str(ids)[1:-1]
        cur.execute("SELECT * FROM users WHERE id in ({0})".format(idlists))
        thisplayerlist = cur.fetchall()
    else:
        thisplayerlist = []

    thisHash = falseHash(gameID)
    thisUser = session.get("user_id")
    thisUser = str(thisUser)[1:-2]
    if str(gameGMID) == str(thisUser):
        thisisGM = True
        thisisPlayer = False
    else:
        thisisGM = False
        cur.execute("SELECT * FROM players WHERE rpgID = ? AND usersID = ?" , [gameID, thisUser])
        rows = cur.fetchone()
        if rows != None:
            thisisPlayer = True
        else:
            thisisPlayer = False
    currentTime = datetime.now()
    print(currentTime)
    try:
        thisUser = session.get("user_id")
        thisUser = str(thisUser)[1:-2]
        cur.execute("SELECT * FROM users WHERE id = ?", [thisUser])
        rows3 = cur.fetchone()
    except:
        flash("Please log in")
        con.close()
        return redirect("/")
    thisTimeZone = rows3[5]
    currentTime = currentTime + timedelta(hours=int(thisTimeZone))
    print(currentTime)
    try:
        cur.execute("SELECT * FROM rpgmeetings WHERE rpgID = ? AND MeetingTime > ? ORDER BY MeetingTime ASC",
            [gameID, str(currentTime)])
        scheduleRows = cur.fetchall()
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

    con.close()
    #print([gameName, gameDescription, thisGMName, gameID, thisplayerlist, thisHash, thisisGM, thisisPlayer, nextMeeting, meetingsList, thisTimezone])
    return render_template("rpg.html", rpgname = gameName, rpgDescription = gameDescription, gmName = thisGMName,
        rpgID = gameID, playerlist = thisplayerlist, inviteHash = thisHash, isGM = thisisGM, isPlayer = thisisPlayer,
        nextMeeting = nextMeeting, meetingsList = meetingsList, timezone = thisTimezone)

@app.route("/dropPlayer", methods = ["POST", "GET"])
def dropPlayer():
    con = lite.connect("finalproject.db")
    cur = con.cursor()

    if request.method == "POST":
        thisgameID = request.form.get("rpgID")
        thisplayerID = request.form.get("playerID")
        if thisgameID is None:
            flash("Invalid ID")
            con.close()
            return redirect("/")
        cur.execute("SELECT * FROM rpgs WHERE id = ?", [thisgameID])
        rows = cur.fetchone()
        #If the GM of the RPG accessed isn't the same as the currently logged in user, attempts to drop users will fail
        thisUser = session.get("user_id")
        thisUser = str(thisUser)[1:-2]
        if (str(rows[1]) != thisUser):
            flash("You cannot remove players from games that you aren't GMing")
            con.close()
            return redirect("/")
        else:
            print("GameID:")
            print(thisgameID)
            print("PlayerID:")
            print(thisplayerID)
            cur.execute("DELETE FROM players WHERE rpgID = ? AND usersID = ?", [thisgameID, thisplayerID])
            con.close()
            return redirect("rpg?rpgID="+thisgameID)
    else:
        thisID = request.args.get('rpgID')
        thisPlayer = request.args.get('playerID')
        
        cur.execute("SELECT * FROM users WHERE id = ?", [thisPlayer])
        rows = cur.fetchone()
        thisplayerName = rows[1]


        cur.execute("SELECT * FROM rpgs WHERE id = ?", [thisID])
        rows = cur.fetchone()
        thisRPGName = rows[2]
        
        con.close()
        return render_template("dropPlayer.html", rpgID = thisID, playerID = thisPlayer, playerName = thisplayerName, RPGName = thisRPGName)

@app.route("/rpgedit", methods = ["POST", "GET"])
def rpgedit():
    con = lite.connect("finalproject.db")
    cur = con.cursor()
    if request.method == "POST":
        if not request.form.get("rpgID"):
            flash("You shouldn't be here")
            con.close()
            return redirect("/")
        if not request.form.get("gameName"):
            flash("Please provide a name for your RPG")
            con.close()
            return redirect("/")
        if not request.form.get("gameDescription"):
            flash("Please provide a description for your RPG")
            con.close()
            return redirect("/")

        rpgID = request.form.get("rpgID")
        newgameDescription = request.form.get("gameDescription")
        newgameName = request.form.get("gameName")


        cur.execute("UPDATE rpgs SET name = ?, description = ? WHERE id = ?",
            [request.form.get("gameName"), request.form.get("gameDescription"), request.form.get("rpgID")])

        con.close()
        return redirect("/")
    else:
        thisID = request.args.get('rpgID')
        cur.execute("SELECT * FROM rpgs WHERE id = ?", [thisID])
        rows = cur.fetchone()

        thisUser = session.get("user_id")
        thisUser = str(thisUser)[1:-2]
        gameGMID = rows[1]

        if (str(gameGMID) != thisUser):
            flash("You cannot edit RPGs that you are not the GM for")
            con.close()
            return redirect("/")

        gameName = rows[2]
        gameDescription = rows[3]
        gameID = rows[0]


        cur.execute("SELECT * FROM users WHERE id = ?", [gameGMID])
        gmrows = cur.fetchone()
        thisGMName = gmrows[1]

        cur.execute("SELECT * FROM players WHERE rpgID = ?", [gameID])
        playerIDs = cur.fetchall()
        if playerIDs != []:
            ids = []
            for id in playerIDs:
                ids.append(id[0])
            cur.execute("SELECT * FROM users WHERE id in ({0})".format(ids))
            thisplayerlist = cur.fetchall()
        else:
            thisplayerlist = []
        con.close()
        return render_template("rpgedit.html", rpgname = gameName, rpgDescription = gameDescription, gmName = thisGMName, playerlist = thisplayerlist, rpgID = gameID)

@app.route("/deleterpg", methods = ["GET", "POST"])
def deleterpg():
    con = lite.connect("finalproject.db")
    cur = con.cursor()    
    if request.method == "POST":
        gameID = request.form.get("rpgID")
        cur.execute("DELETE FROM rpgs WHERE id = ?", [gameID])
        cur.execute("DELETE FROM players WHERE rpgID = ?", [gameID])
        con.close()
        return redirect("/")
    else:
        gameID = request.args.get('rpgID')
        cur.execute("SELECT * FROM rpgs WHERE id = ?", [gameID])
        rows = cur.fetchone()

        thisUser = session.get("user_id")
        thisUser = str(thisUser)[1:-2]
        gameGMID = rows[1]

        if (str(gameGMID) != thisUser):
            flash("You cannot delete RPGs that you are not the GM for")
            con.close()
            return redirect("/")
        con.close()
        return render_template("deleterpg.html", RPGName = rows[2], rpgID = rows[0])

@app.route("/invite", methods = ["GET", "POST"])
def invite():
    if request.method == "POST":
        if session.get("user_id") is None:
            flash("Must login or register before joining this RPG.")
            session["followUp"] = "/invite?code="+str(request.form.get("gameHash"))
            return redirect("/login")
        else:
            con = lite.connect("finalproject.db")
            cur = con.cursor()


            gameID = int(dehash(request.form.get("gameHash")))
            thisUser = session.get("user_id")
            thisUser = str(thisUser)[1:-2]

            rows = cur.execute("SELECT * FROM players WHERE rpgID = ? AND usersID = ?", [gameID, thisUser])
            rows = cur.fetchone()
            if rows == None:
                cur.execute("INSERT INTO players (rpgID, usersID) VALUES (?, ?)", [gameID, thisUser])
                destination = "/rpg?rpgID="+str(gameID)
                flash("You've joined this RPG!")
                con.close()
                return redirect(destination)
            else:
                destination = "/rpg?rpgID="+str(gameID)
                flash("You cannot join this RPG because you are already in this RPG")
                con.close()
                return redirect(destination)
    else:
        thisgameHash = request.args.get('code')
        gameID = int(dehash(thisgameHash))

        con = lite.connect("finalproject.db")
        cur = con.cursor()

        cur.execute("SELECT * FROM rpgs WHERE id = ?", [gameID])
        rows = cur.fetchone()

        con.close()
        return render_template("invite.html", RPGName = rows[2], Description = rows[3], gameHash = thisgameHash)

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

            con = lite.connect("finalproject.db")
            cur = con.cursor()
            cur.execute("INSERT INTO rpgMeetings (Location, MeetingTime, rpgID, timezone) VALUES (?, ?, ?, ?)",
                [locationAttempt, str(meetingDateTime), thisID, request.form.get("timezone")])
            flash("Meeting added")
            con.close()
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

            con = lite.connect("finalproject.db")
            cur = con.cursor()
            thisUser = session.get("user_id")
            thisUser = str(thisUser)[1:-2]

            db.execute("SELECT * FROM users WHERE id = ?", [thisUser])
            GMTime = cur.fetchone()
            try:
                meetingDateTime = datetime.strptime(combined, '%m/%d/%Y %H:%M') - timedelta(hours=int(GMTime[0]["timezone"]))
            except:
                flash("You didn't give date or time in a valid format. Please try again.")
                con.close()
                return render_template("schedule.html", gameID = thisID,
                    dateAttempt = dateAttempt, timeAttempt = timeAttempt, locationAttempt = locationAttempt)

            print(str(meetingDateTime))
            cur.execute("SELECT usersID FROM players WHERE rpgID = ?", [thisID])
            rows = fetchall()
            ids = []
            if rows != []:
                for id in rows:
                    if str(id[0]) != thisUser:
                        ids.append(id[0])
            cur.execute("SELECT * FROM users WHERE id in ({0})".format(ids))
            rows2 = cur.fetchall()
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

        con = lite.connect("finalproject.db")
        cur = con.cursor()
        cur.execute("SELECT * FROM rpgs WHERE id = ?", [thisID])
        rows = cur.fetchone()
        thisUser = session.get("user_id")
        thisUser = str(thisUser)[1:-2]

        if (str(rows[1]) != thisUser):
            flash("You cannot edit RPGs that you are not the GM for")
            return redirect("/")
        cur.execute("SELECT * FROM users WHERE id = ?", [thisUser])
        rows = cur.fetchone()
        return render_template("schedule.html", gameID = thisID, timezone = rows[5])

@app.route("/leaveRPG", methods = ["POST", "GET"])
def leaveRPG():
    if request.method == "POST":
        thisID = request.form.get("rpgID")
        if thisID is None:
            flash("Invalid ID")
            return redirect("/")

        con = lite.connect("finalproject.db")
        cur = con.cursor()    
        thisUser = session.get("user_id")
        thisUser = str(thisUser)[1:-2]


        cur.execute("SELECT * FROM players WHERE id = ? AND usersID = ?", [thisID, thisUser])
        rows = cur.fetchone()
        if rows == None:
            flash("You are not in this RPG")
        else:
            cur.execute("DELETE FROM players WHERE id = ? AND usersID = ?", [thisID, thisUser])
        con.close()
        return redirect("/")
    else:
        thisID = request.args.get('rpgID')
        return render_template("leaveRPG.html", rpgID = thisID)