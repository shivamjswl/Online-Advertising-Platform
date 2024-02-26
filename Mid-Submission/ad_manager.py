# importing System dependencies and required flask modules
import sys
import os
import json
import datetime
import mysql.connector
from datetime import datetime as dt
from pykafka import KafkaClient
from pykafka.common import OffsetType
from pykafka.exceptions import SocketDisconnectedError, LeaderNotAvailable

class KafkaMySQLSink:
    def __init__(self, kafka_bootstrap_server, kafka_topic_name, database_host,database_username, database_password,database_name):
        # We need to Initialize the Kafka Consumer
        kafka_client = KafkaClient(kafka_bootstrap_server)
        self.consumer = kafka_client \
            .topics[kafka_topic_name] \
            .get_simple_consumer(consumer_group="campaign_id",auto_offset_reset=OffsetType.LATEST)

        # We need to Initialize the MySQL database connection
        self.db = mysql.connector.connect(host=database_host,user=database_username,password=database_password,database=database_name)
        # Process single row
    def process_row(self, AdsInfo):
        # Get the db cursor
        db_cursor = self.db.cursor()
        # DB query for supporting UPSERT operation (update + insert)
        sql = ("INSERT INTO ads(text,category,keywords,campaignID,status,targetGender,targetAgeStart,targetAgeEnd,targetCity,targetState,targetCountry,targetIncomeBucket,targetDevice,cpc,cpa,cpm,budget,currentSlotBudget,dateRangeStart,dateRangeEnd,timeRangeStart,timeRangeEnd) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE  text =%s, category =%s,keywords =%s,status =%s,targetGender =%s,targetAgeStart =%s,targetAgeEnd =%s,targetCity =%s,targetState =%s,targetCountry =%s,targetIncomeBucket =%s,targetDevice =%s,cpc =%s,cpa =%s,cpm =%s, budget =%s,currentSlotBudget =%s,dateRangeStart =%s, dateRangeEnd =%s,timeRangeStart =%s,timeRangeEnd =%s");
        AdsInfo["text"] = AdsInfo["text"].replace("'", "")
        val = (AdsInfo["text"],AdsInfo["category"],AdsInfo["keywords"],AdsInfo["campaign_id"],AdsInfo["status"],AdsInfo["target_gender"],AdsInfo["target_age_range"]["start"],AdsInfo["target_age_range"]["end"],AdsInfo["target_city"],AdsInfo["target_state"],AdsInfo["target_country"],AdsInfo["target_income_bucket"],AdsInfo["target_device"],AdsInfo["cpc"],AdsInfo["cpa"],AdsInfo["cpm"],AdsInfo["budget"],AdsInfo["current_slot_budget"],AdsInfo["date_range"]["start"],AdsInfo["date_range"]["end"],AdsInfo["time_range"]["start"],AdsInfo["time_range"]["end"],AdsInfo["text"],AdsInfo["category"],AdsInfo["keywords"],AdsInfo["status"],AdsInfo["target_gender"],AdsInfo["target_age_range"]["start"],AdsInfo["target_age_range"]["end"],AdsInfo["target_city"],AdsInfo["target_state"],AdsInfo["target_country"],AdsInfo["target_income_bucket"],AdsInfo["target_device"],AdsInfo["cpc"],AdsInfo["cpa"],AdsInfo["cpm"],AdsInfo["budget"],AdsInfo["current_slot_budget"],AdsInfo["date_range"]["start"],AdsInfo["date_range"]["end"],AdsInfo["time_range"]["start"],AdsInfo["time_range"]["end"]);
        db_cursor.execute(sql, (val) );    
        # We will commit the operation, so that it reflects globally
        self.db.commit()

    # Process kafka queue messages
    def process_events(self):
        def dervied_attribute(adInfo):
            def SlotBudgetCalculation(budget,dateperiod,timeperiod):
                Slotslist = []
                start = dt.strptime(dateperiod["start"]+" "+timeperiod["start"], "%Y-%m-%d %H:%M:%S")
                end = dt.strptime(dateperiod["end"]+" "+timeperiod["end"], "%Y-%m-%d %H:%M:%S")
                while start <= end:
                    Slotslist.append(start)
                    start += datetime.timedelta(minutes=10)
                return (float(budget)/len(Slotslist))

            # Setting derived Types like status,cpm,cuurent_slot_budget:
            adInfo["status"] = "INACTIVE" if adInfo["action"] == "Stop Campaign" else "ACTIVE"
            adInfo["cpm"] = 0.0075 * float(adInfo["cpc"]) + 0.0005 * float(adInfo["cpa"])
            adInfo["current_slot_budget"] = SlotBudgetCalculation(adInfo["budget"],adInfo["date_range"],adInfo["time_range"])
            return adInfo
        try:
            for queue_message in self.consumer:
                if queue_message is not None:
                    msg = json.loads(queue_message.value)
                    AdsInfo = dervied_attribute(msg)
                    sep = " | "
                    print(AdsInfo["campaign_id"],sep,AdsInfo["action"],sep,AdsInfo["status"])
                    self.process_row(AdsInfo)

        # In case Kafka connection errors, we will restart consumer and start processing
        except (SocketDisconnectedError, LeaderNotAvailable) as e:
            self.consumer.stop()
            self.consumer.start()
            self.process_events()
            
    def __del__(self):
        # Cleanup of consumer and database connection before termination
        self.consumer.stop()
        self.db.close()
                   

if __name__ == "__main__":
    
    # Validate Command line arguments
    if len(sys.argv) != 7:
        print("Usage: ad_manager.py <kafka_bootstrap_server> <kafka_topic> "
        "<database_host> <database_username> <database_password> <database_name>")
        exit(-1)
        
    kafka_bootstrap_server = sys.argv[1]
    kafka_topic = sys.argv[2]
    database_host = sys.argv[3]
    database_username = sys.argv[4]
    database_password = sys.argv[5]
    database_name = sys.argv[6]

    ad_manager = None    
    kafka_mysql_sink = None    
    try:
        kafka_mysql_sink = KafkaMySQLSink(kafka_bootstrap_server, kafka_topic, database_host, database_username,database_password, database_name)
        kafka_mysql_sink.process_events()            
    except KeyboardInterrupt:
        print('KeyboardInterrupt, exiting...')    
    finally:
        if kafka_mysql_sink is not None:
            del kafka_mysql_sink