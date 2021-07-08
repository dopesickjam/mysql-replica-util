import mysql.connector
from dotenv import load_dotenv
import os
import time
import requests

load_dotenv()
mysql_host = os.getenv('mysql_host')
mysql_user = os.getenv('mysql_user')
mysql_pass = os.getenv('mysql_pass')
mysql_port = os.getenv('mysql_port')
replica_delay = int(os.getenv('replica_delay'))
tg_token = os.getenv('tg_token')
tg_chat = os.getenv('tg_chat')

def mysqlConn():
  try:
    msql = mysql.connector.connect(
      host=mysql_host,
      port=mysql_port,
      user=mysql_user,
      password=mysql_pass
    )
    return msql
  except mysql.connector.errors.InterfaceError:
    sendTg("Cannot connect to the replica")

def getInfo(msql):
  mycursor = msql.cursor()
  mycursor.execute("show slave status;")
  info = mycursor.fetchall()
  mycursor.close()
  if not info:
    sendTg("Cannot get info from replica")
  else:
    replica_info = {
      'Slave_IO_Running': info[0][10],
      'Slave_SQL_Running': info[0][11],
      'Last_Errno': info[0][18],
      'Last_Error': info[0][19],
      'Seconds_Behind_Master': info[0][32],
      'Last_IO_Errno': info[0][34],
      'Last_IO_Error': info[0][35],
      'Last_SQL_Errno': info[0][36],
      'Last_SQL_Error': info[0][37],
      'SQL_Delay': info[0][42],
      'SQL_Remaining_Delay': info[0][43],
      'Slave_SQL_Running_State': info[0][43]
    }
    return replica_info

def cannonBall(msql):
  mycursor = msql.cursor()
  mycursor.execute("stop slave;")
  mycursor.execute("SET GLOBAL SQL_SLAVE_SKIP_COUNTER = 1;")
  mycursor.execute("start slave;")
  mycursor.close()

def sendTg(reason, replica_info=None):
  if replica_info:
    message = '<b>Replication Error</b>\n' + \
              f'<b>Reason</b>: <i>{reason}</i>\n\n' + \
              '<b>Info</b>\n' + \
              f"<b>Slave_IO_Running</b>: {replica_info['Slave_IO_Running']}\n" + \
              f"<b>Slave_SQL_Running</b>: {replica_info['Slave_SQL_Running']}\n" + \
              f"<b>Last_Errno</b>: {replica_info['Last_Errno']}\n" + \
              f"<b>Last_Error</b>: {replica_info['Last_Error']}\n" + \
              f"<b>Seconds_Behind_Master</b>: {replica_info['Seconds_Behind_Master']}\n" + \
              f"<b>Last_IO_Errno</b>: {replica_info['Last_IO_Errno']}\n" + \
              f"<b>Last_IO_Error</b>: {replica_info['Last_IO_Error']}\n" + \
              f"<b>Last_SQL_Errno</b>: {replica_info['Last_SQL_Errno']}\n" + \
              f"<b>Last_SQL_Error</b>: {replica_info['Last_SQL_Error']}\n" + \
              f"<b>SQL_Delay</b>: {replica_info['SQL_Delay']}\n" + \
              f"<b>SQL_Remaining_Delay</b>: {replica_info['SQL_Remaining_Delay']}\n" + \
              f"<b>Slave_SQL_Running_State</b>: {replica_info['Slave_SQL_Running_State']}\n"
  else:
    message = '<b>Replication Error</b>\n' + \
            f'<b>Reason</b>: <i>{reason}</i>'

  send_text = 'https://api.telegram.org/bot' + tg_token + '/sendMessage?chat_id=' + tg_chat + '&text=' + message + '&parse_mode=HTML'
  response = requests.get(send_text)
  # print(response.text)

msql = mysqlConn()
replica_info = getInfo(msql)

if replica_info['Seconds_Behind_Master'] == None:
  sendTg("Cannot connect to the master", replica_info)
elif replica_info['Seconds_Behind_Master'] >= replica_delay:
  sendTg("Seconds Behind Master is HIGH", replica_info)
  while True:
    cannonBall(msql)
    time.sleep(320)
    replica_info = getInfo(msql)
    if replica_info['Seconds_Behind_Master'] == 0:
      sendTg("OK", replica_info)
      break
    else:
      sendTg("Still has replication delay", replica_info)
else:
  print(f'cron is successed, Seconds_Behind_Master = {replica_info["Seconds_Behind_Master"]}')