import yaml
import logging
import mysql.connector as mysql
import logging.handlers

from sys import exit
#########################

class RecurringCharging:
    def __init__(self,recurringchargingObject):
        self.dictRecurringCharging = recurringchargingObject
        self.logger = logging.getLogger(self.__class__.__name__)

    def insert(self, db):
        self.logger.debug("Insert into table [" + self.dictRecurringCharging["table"] + "] with offer_external_id: [" + str(self.dictRecurringCharging["offer_external_ID"]) + "]")
        #db = mysql.connect(user='vocs-silver', password='AhKDYGkBJPre26cBm1Tukg==', host='10.60.142.54', database='vocs')
        #db = mysql.connect(user='root', password='123456a@', host='10.60.145.16',database='vocs')
        cur = db.cursor()
        cur.execute("INSERT INTO `recurring_charging` (`BILLING_CYCLE_TYPE_ID`, `EVENT_ID`, `REMARK`, `PRIORITY`, `NOTIFY_DAY_BEFORE`, `NOTIFY_BALANCE_QUOTA`, `NOTIFY_END_TIME`, `NOTIFY_TIME_FAIL`, `offer_id`, `TRIGGER_ID`, `sent_trigger`"
                    ", `sent_trigger_fail`, `trigger_id_enough`, `trigger_id_not_enough`, `TRIGGER_ID_SUSPEND`, `trigger_id_fail`, `notify_start_time`, `time_retry`, `re_active`) VALUES (NULL, 1003, NULL, NULL, 1, NULL, 540, NULL, "
                    "(select offer_id from offer where offer_external_id= {0}), 213, {1}, 0, 216, 215, 217, 214, 480, NULL, 1);".format(self.dictRecurringCharging["offer_external_ID"],self.dictRecurringCharging["sent_trigger"]))
        db.commit()
        self.logger.debug("Insert completely")

    def run(self, db):
        self.insert(db)
        

import logging.config

if __name__ == '__main__':
    db = mysql.connect(user='anhnn91', password='nhat1998', host='127.0.0.1', database='anhnn91')
    #with open('../conf/logging-test.yml', 'r') as f:
    with open('conf/logging-test.yml', 'r') as f:
        try:
            _logconfig = yaml.safe_load(f.read())
            logging.config.dictConfig(_logconfig)
        except yaml.YAMLError as exc:
            print(exc)
            exit(1)
    logger = logging.getLogger(__name__)

    with open("Table/templaterecurringcharging.yml", "r") as stream:
        try:
            dictConfig = yaml.safe_load(stream)
            for i in range(0,len(dictConfig)):
                print(dictConfig[i]["AutoInteractDB"])
                if dictConfig[i].get("AutoInteractDB") is None:
                    print("May Interaction is not in order")
                    continue
                if dictConfig[i]["AutoInteractDB"]["table"] == "Recurring Charging":
                    print("run to insert into table recurring charging with offer_external_id [" + str(dictConfig[i]["AutoInteractDB"]["offer_external_ID"]) + "]")
                    recurringcharging = RecurringCharging(dictConfig[i]["AutoInteractDB"])
                    recurringcharging.run(db)
            print("Finish")
        except yaml.YAMLError as exc:
            print(exc)
    exit(0)