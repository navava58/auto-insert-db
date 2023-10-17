import yaml
import logging
import mysql.connector as mysql
import logging.handlers
from sys import exit
#########################

class BeforeRecurring:
    def __init__(self,beforerecurringObject):
        self.dictBeforeRecurring = beforerecurringObject
        self.logger = logging.getLogger(self.__class__.__name__)

    def insert(self, db):
        self.logger.debug("Insert into table [" + self.dictBeforeRecurring["table"] + "] with offer_external_id: [" + str(self.dictBeforeRecurring["offer_external_ID"]) + "]")
        #db = mysql.connect(user='vocs-silver', password='AhKDYGkBJPre26cBm1Tukg==', host='10.60.142.54', database='vocs')
        #db = mysql.connect(user='root', password='123456a@', host='10.60.145.16',database='vocs')
        #db = mysql.connect(user='anhnn91', password='nhat1998', host='127.0.0.1', database='anhnn91')
        cur = db.cursor()
        cur.execute("INSERT INTO triggerpolicy_condition_goto__buildertype (condition_check_goto,gotoBuilderType,item_id,remarks)  select 'triggerMsg.getTriggerId() == 1017  && Integer.parseInt(triggerMsg.getCraMsg().getField(7101).toString())==2  &&  CDRUtils.checkValueOfListFieldIDInListInput(triggerMsg, 1001, new  long[]{{{0}}})' ,  '{1}'  , 2 , 'builderTypeSms' from dual ;".format(self.dictBeforeRecurring["offer_external_ID"],self.dictBeforeRecurring["sms_template_code"]))
        cur.execute("INSERT INTO triggerpolicy_build_sms (needMapField,smsRouteId,smsTemplateCode,name_builder,src_class,des_class,id_link_to_base_event,buildertype) select 'true', {0}, '{1}', 'nameBuilder', 'TriggerMsg', 'SmsNotifyRequest', 1, {1} from dual ;".format(self.dictBeforeRecurring["smsRouteId"],self.dictBeforeRecurring["sms_template_code"]))
        cur.execute("INSERT INTO sms_notify_template(MESSAGE_TEMPLATE,LANG_ID,SMS_TEMPLATE_CODE,DOMAIN_ID) SELECT  '{0}', 57 , {1}, 1  from dual ;".format(self.dictBeforeRecurring["message_template"],self.dictBeforeRecurring["sms_template_code"]))
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

    with open("Table/templatebeforerec.yml", "r") as stream:
        try:
            dictConfig = yaml.safe_load(stream)
            for i in range(0,len(dictConfig)):
                print(dictConfig[i]["AutoInteractDB"])
                if dictConfig[i].get("AutoInteractDB") is None:
                    print("May Interaction is not in order")
                    continue
                if dictConfig[i]["AutoInteractDB"]["table"] == "BeforeRecurring":
                    print("run to insert into table recurring charging with offer_external_id [" + str(dictConfig[i]["AutoInteractDB"]["offer_external_ID"]) + "]")
                    beforerecurring = BeforeRecurring(dictConfig[i]["AutoInteractDB"])
                    beforerecurring.run(db)
            print("Finish")
        except yaml.YAMLError as exc:
            print(exc)
    exit(0)