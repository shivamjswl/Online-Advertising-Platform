# importing System dependencies and required flask modules
import sys
import flask
from flask import request, jsonify
import uuid
from flask import abort
import mysql.connector
import datetime

# AdServer Class with all neccessary actions to be performed within the class
class AdServer:

    def __init__(self, database_host, database_username, database_password, database_name):
        # we will initialize the MySQL database connection
        self.db = mysql.connector.connect(
            host=database_host,user=database_username,password=database_password,database=database_name
            )

    # This will fetch details of auction winner and cost details like CPM, CPC and CPA of second highest bidder.
    def fetchAds(self):

        # Initialize DB cursor
        db_cursor = self.db.cursor()

        # Auction cost details and winner details SQL statements
        sql_fetch_auctionCost = "select cpm,cpc,cpa from ( select * from ads "
        sql_fetch_auctionWin = "select *  from ( select * from ads "

        # to select active ads and to eliminate expired DateTime range
        conditionStatement = ("where status = 'active'"
        " and  CURRENT_TIMESTAMP() between TIMESTAMP(dateRangeStart,timeRangeStart) and TIMESTAMP(dateRangeEnd,timeRangeEnd) ")

        if self.device != "All":
            conditionStatement += " and targetDevice = '" + self.device  + "' "

        if self.city != "All":
            conditionStatement += " and targetCity = '" + self.city  + "' "

        if self.state != "All":
            conditionStatement += " and targetState = '" + self.state  + "' "

        # to select cost details from the second highest bidder
        sql_fetch_auctionCost += conditionStatement + " order by cpm desc limit 2 ) as temp order by cpm limit 1;"

        # Gathering details from the Winner AD
        sql_fetch_auctionWin += conditionStatement + " order by cpm desc limit 2) as temp limit 1;"

        # Retrieve auction cost for campaign
        db_cursor.execute(sql_fetch_auctionCost)
        self.DecidedAuctionCost =  db_cursor.fetchall()


        # Retrieve auction ad details
        db_cursor.execute(sql_fetch_auctionWin)
        self.adDetails =  db_cursor.fetchall()


    # we will insert the details of winner with the cost details of second highest bidder into the served_ads Table.
    def Served_entry(self):

        db_cursor = self.db.cursor()

        # Insert statement add into 
        if len(self.adDetails) != 0 and len(self.DecidedAuctionCost[0]) != 0:

            currentTimeStamp = datetime.datetime.now().replace(microsecond=0)
            startDateTime = datetime.datetime.combine(self.adDetails[0][18],(datetime.datetime.min + self.adDetails[0][20]).time())
            endDateTime = datetime.datetime.combine(self.adDetails[0][19],(datetime.datetime.min + self.adDetails[0][21]).time())
            
            # SQL insert Operation Statement
            sql = ("INSERT INTO served_ads("
                    "requestID ,"
                    "campaignID ,"
                    "userID ,"
                    "auctionCPM ,"
                    "auctionCPC ,"
                    "auctionCPA ,"
                    "targetAgeRange ,"
                    "targetLocation ,"
                    "targetGender ,"
                    "targetIncomeBucket ,"
                    "targetDeviceType ,"
                    "campaignStartTime ,"
                    "campaignEndTime ,"
                    "userFeedbackTimeStamp)"
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)" 
                    )
            # SQL insert Operation Values
            val = (
                self.request_id,
                self.adDetails[0][3],
                self.user_id,
                self.DecidedAuctionCost[0][0],
                self.DecidedAuctionCost[0][1],
                self.DecidedAuctionCost[0][2],
                str(self.adDetails[0][6]) +"-"+ str(self.adDetails[0][7]),
                self.adDetails[0][8] +", "+ self.adDetails[0][9] +" and "+ self.adDetails[0][10],
                self.adDetails[0][5],
                self.adDetails[0][11],
                self.adDetails[0][12],
                startDateTime,
                endDateTime,
                currentTimeStamp
                )

            # Executing the sql statement
            db_cursor.execute(sql, val)

            # commiting changes to the DB
            self.db.commit()

    # Process function which calls FetchAds and Served_entry
    def ad_process(self):
        self.fetchAds()
        self.Served_entry()

    # Cleanup of database connection before termination
    def __del__(self):
        self.db.close()


if __name__ == "__main__":

    # Validating Command line arguments
    if len(sys.argv) != 5:
        print("Usage: <database_host> <database_username> <database_password> <database_name>")
        exit(-1)

    # Assiging arguments with meaning full names
    database_host = sys.argv[1]
    database_username = sys.argv[2]
    database_password = sys.argv[3]
    database_name = sys.argv[4]

    try:
        ad_server_object = AdServer(database_host,database_username,database_password,database_name)

        # Basic Flask COnfiguration
        app = flask.Flask(__name__)
        app.config["DEBUG"] = True;
        app.config["RESTFUL_JSON"] = {"ensure_ascii":False}

        # Http Get request  processing
        @app.route('/ad/user/<user_id>/serve', methods=['GET'])
        def serve(user_id):
            # 
            if "state" not in request.args:
                return abort(400)

            if "city" not in request.args:
                 return abort(400)
            
            if "device_type" not in request.args:
                return abort(400)

            # Generate the request identifier
            request_id = str(uuid.uuid1())

            # Initialzing variables to AdServer Class object
            ad_server_object.user_id = user_id
            ad_server_object.request_id = request_id
            ad_server_object.state = request.args["state"]
            ad_server_object.city = request.args["city"]
            ad_server_object.device = request.args["device_type"]

            # Ad server process initiation
            ad_server_object.ad_process()
            
            # Response for successful selected AD
            if len(ad_server_object.adDetails) != 0:
                return jsonify({
                    "request_id": request_id,
                    "text": ad_server_object.adDetails[0][0]
                    })

            # Response for failure selected AD
            return jsonify({
                "status": "success",
                "request_id": request_id,
                "Sorry": "No ad to serve"
                })

        # Hosting web service at localhost and port 5000 
        app.run(host="0.0.0.0", port=5000)

    except KeyboardInterrupt:
        print("press control-c again to quit")

    finally:
        if ad_server_object is not None:
            del ad_server_object