import os
import logging
import pyrogram
from decouple import config
import psycopg2, requests
from pyrogram.filters import user
from decimal import Decimal
from urllib.parse import urlparse

logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
                    level=logging.WARNING)

# vars
APP_ID = os.environ.get("API_ID")
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
DATABASE_URI = os.environ.get("DATABASE_URL")
AUTH_IDS = set(int(x) for x in os.environ.get("AUTH_IDS").split())
ADMIN_IDS = set(int(x) for x in os.environ.get("ADMIN_IDS").split())


TWILIO_SID = "ACf15c73e78baba374db270f259ded078c"
TWILIO_AUTHTOKEN = "no"
TWILIO_SERVICEID = "MG962b4acdc6e5cf23b4e601d61e87b350"
DEDUCTION_PER_SEND = 0.02
AMOUNT_PER_CREDIT = 0.02


result = urlparse(DATABASE_URI)
username = result.username
password = result.password
database = result.path[1:]
hostname = result.hostname
port = result.port
mydb = psycopg2.connect(
    database = database,
    user = username,
    password = password,
    host = hostname,
    port = port
)
mycursor = mydb.cursor()

###Create table
mycursor.execute("select exists(select * from information_schema.tables where table_name=%s)", ('premium',))
if mycursor.fetchone()[0] != True:
  mycursor.execute('''CREATE TABLE premium
        (ID SERIAL PRIMARY KEY     NOT NULL,
        userid  TEXT    NOT NULL,
        credits TEXT     NOT NULL);''')
  mydb.commit()
  

def num(s):
    try:
        return int(s)
    except ValueError:
        return float(s)
      
def isPremium(userid):
  if userid in ADMIN_IDS:
    return True
  resp = mycursor.execute(f"SELECT * FROM premium WHERE userid = '{userid}'")
  result = mycursor.fetchall()
  mydb.commit()
  
  if result:
    return True
  else:
    return False

def addPremium(userid,credits):
    if isPremium(userid) != True:
        mycursor.execute(f"INSERT INTO premium (userid, credits) VALUES ('{userid}','{float(credits)}')")
        mydb.commit()
        
        return True
    elif isPremium(userid) == True:
        currentcredits = getCredits(userid)
        newcredits = num(currentcredits)+num(credits)
        
        mycursor.execute(f"UPDATE premium SET credits = '{newcredits}' WHERE userid = '{userid}'")
        mydb.commit()
        
        return True

def setCredits(userid,credits):
    if isPremium(userid) != True:
        return False
    elif isPremium(userid) == True:
        mycursor.execute(f"UPDATE premium SET credits = '{credits}' WHERE userid = '{userid}'")
        mydb.commit()
        
        return True        

def banPremium(userid):
  if userid in ADMIN_IDS:
    return False
  mycursor.execute(f"DELETE FROM premium WHERE userid='{userid}'")
  mydb.commit()
  
  return True

def getCredits(userid):
  mycursor.execute(f"SELECT credits FROM premium WHERE userid = '{userid}'")
  result = mycursor.fetchall()
  mydb.commit()
  
  return result[0][0]

def costofLeads(totalleads):
  return totalleads*DEDUCTION_PER_SEND

def hasSufficientCredits(userid,totalleads):
  usercredits = getCredits(userid)
  cost = costofLeads(totalleads)
  
  if userid in ADMIN_IDS:
    return True
  elif num(usercredits) >= cost:
    return True
  else:
    return False

def deductCredits(userid,totalleads):
  if userid in ADMIN_IDS:
    return True
  usercredits = getCredits(userid)
  costtotal = costofLeads(totalleads)
  newcredits = Decimal(str(usercredits))-Decimal(str(costtotal))
  
  mycursor.execute(f"UPDATE premium SET credits = '{newcredits}' WHERE userid = '{userid}'")
  mydb.commit()
  
  
async def sendSMS(number,smsmessage):
    smsmessage = smsmessage.replace('{number}',number)
    
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    postdata = {

    'To': number,
    'Body': smsmessage,
    'MessagingServiceSid': TWILIO_SERVICEID

    }
    postsms = requests.post(f'https://api.twilio.com/2010-04-01/Accounts/{TWILIO_SID}/Messages.json', headers=headers, data=postdata, auth=(TWILIO_SID, TWILIO_AUTHTOKEN))
    
    if postsms.json()['status'] == 'accepted':
        return True
    else:
        return False
  

if __name__ == "__main__" :
    print("Starting Bot...")
    plugins = dict(root="PyroBot/plugins")
    app = pyrogram.Client(
        "Ninja",
        bot_token=BOT_TOKEN,
        api_id=APP_ID,
        api_hash=API_HASH,
        plugins=plugins
    )
    print("Bot has been successfully deployed!")
    app.run()
    

    
    
