#!/usr/bin/env python3
from gevent import monkey
monkey.patch_all()
import asyncio
from datetime import datetime, timezone, timedelta
from email.message import EmailMessage
from functools import wraps
from getpass import getpass
from panoramisk import Manager
from werkzeug.middleware.proxy_fix import ProxyFix
import sys
import pymsteams
import os
import requests
import smtplib
import json
import ssl
import httpx
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
import threading 
from flask import Flask, render_template, Response, jsonify 
import time 


REAL_TIME_DATA = {
    "current_queue_count": 0,
    "longest_wait_time_seconds": 0,
    "hourly_report": { 
        "total_calls": 0,
        "avg_wait_time_seconds": 0,
        "calls_by_agent": {},
        "abandoned_calls": [] 
    }, 
    "daily_report": {
        "total_calls": 0,
        "avg_wait_time_seconds": 0,
        "abandoned_calls_count": 0,
        "calls_by_agent": {},
        "abandoned_calls_details": [],
        "agent_avg_talk_time": {} 
    },
    "calls_in_queue": [], 
    "call_log": [],
    "live_active_calls": [], 
    "parked_calls": [] 
}


ACTIVE_CALL_CW_CACHE = {}

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout) # This forces logs to the container stream
    ]
)

logger = logging.getLogger(__name__)



app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

manager_loop = asyncio.get_event_loop()



HOST = str(os.getenv("hostname", "Failed getting hostname"))
USERNAME = str(os.getenv("username", "Failed getting username"))
SECRET = str(os.getenv("password", "Failed getting password"))
Auth = str(os.getenv("cw-authorization", "Failed getting auth"))
ClientID = str(os.getenv("CW-Client-ID", "Failed getting client id"))
TENANT_ID = str(os.getenv("tenant-id", "Failed getting tenant id"))
CLIENT_ID = str(os.getenv("client-id", "Failed getting client id"))
CLIENT_SECRET = str(os.getenv("client-secret", "Failed getting client secret"))
TEAM_ID = str(os.getenv("team-id", "Failed getting team id"))
CHANNEL_ID = str(os.getenv("channel-id", "Failed getting channel id"))
CHAT_ID = str(os.getenv("chat-id", "19:"))
SENDER_USER_ID = str(os.getenv("sender-user-id", "Failed getting sender user id"))
SENDER_DISPLAY_NAME = str(os.getenv("sender-display-name", "Failed getting sender display name"))
SMTP_SERVER = str(os.getenv("smtp-server", "outbound-us1.ppe-hosted.com"))
SMTP_PORT = int(os.getenv("smtp-port", 587))
SMTP_SENDER_EMAIL = str(os.getenv("smtp-sender-email"))
SMTP_USER = str(os.getenv("smtp-auth-user"))
SENDER_PASSWORD = str(os.getenv("smtp-auth-password"))
RECIPIENT_EMAILS = os.getenv("recipient-emails", "").split(",") 


QR_QUEUE = str(os.getenv("QR-QUEUE", "15"))
QR_START_HOUR = int(os.getenv("QR-START-HOUR", 7))
QR_END_HOUR = int(os.getenv("QR-END-HOUR", 18))





json_string = os.getenv("techs")
if json_string:
    try:
        tech_dict = json.loads(json_string)
        logging.info("Successfully loaded tech_dict from environment variable.")
    except json.JSONDecodeError as e:
        logging.error(f"Failed to decode JSON from 'techs' env var: {e}")
        tech_dict = {}
else:
    logging.warning("Environment variable 'techs' is not set. Active call agent names may be 'Unknown'.")
    tech_dict = {}



WEBHOOK = os.getenv("TEAMS_WEBHOOK_URL")
WEBHOOK2 = os.getenv("TEAMS_WEBHOOK2_URL")
WEBHOOK3 = os.getenv("TEAMS_WEBHOOK3_URL")
WEBHOOK4 = os.getenv("TEAMS_WEBHOOK4_URL")

manager = Manager(loop=manager_loop,
                  host=HOST,
                  username=USERNAME,
                  secret=SECRET)


teams = pymsteams.connectorcard(WEBHOOK)
teams2 = pymsteams.connectorcard(WEBHOOK2)
teams3 = pymsteams.connectorcard(WEBHOOK3)
teams4 = pymsteams.connectorcard(WEBHOOK4)
teams4.title("QR LOG")


hourly_wait_times = []
daily_wait_times = []
daily_call_counts = {}
hourly_call_counts = {}
call_join_times = {}
call_map = {}
call_states = {}
call_abandoned_count = []
call_abandoned_hourly = []
daily_abandoned_call_objects = []
abandoned_call_namnum = {}
daily_call_log = []


AGENT_TOTAL_TALK_TIME = {}
ANSWERED_CALL_START_TIMES = {}




def in_hours(fn):
    """Only proceed with function if it's not after-hours."""
    @wraps(fn)
    async def wrapper(*args, **kwargs):
        now = datetime.today()
        if (
            now.weekday() < 5 and
            QR_END_HOUR >= now.hour >= QR_START_HOUR
        ):
            await fn(*args, **kwargs)
    return wrapper

def getCID(phoneNumber) -> str:

    if phoneNumber.startswith('1') and len(phoneNumber) == 11:
        phoneNumber = phoneNumber[1:]
        
    if len(phoneNumber) != 10:
        return "Unknown"
        
    url = f"https://api-na.myconnectwise.net/v4_6_release/apis/3.0/company/contacts?childconditions=communicationItems/value+like+{phoneNumber}"
    headers = {
        "Authorization": Auth,
        "ClientID": ClientID,
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if not data:
             return "Unknown"
             
        return (str(data[0]["firstName"]) + " " + str(data[0]["lastName"]) + " (" + str(data[0]["company"]['identifier']) + ")")
    except requests.RequestException as e:
        return "Unknown"
    except IndexError:
        return "Unknown"
    
def getCompanyID(phoneNumber) -> str:
    if phoneNumber.startswith('1') and len(phoneNumber) == 11:
        phoneNumber = phoneNumber[1:]
        
    if len(phoneNumber) != 10:
        return "Unknown"
        
    url = f"https://api-na.myconnectwise.net/v4_6_release/apis/3.0/company/contacts?childconditions=communicationItems/value+like+{phoneNumber}"
    headers = {
        "Authorization": Auth,
        "ClientID": ClientID,
        "Content-Type": "application/json"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if not data:
            return "Unknown"
            
        return str(data[0]["company"].get('id'))
    except requests.RequestException as e:
        return "Unknown"
    except IndexError:
        return "Unknown"
    
def getCompanyNumber(companyID):
    url = f"https://api-na.myconnectwise.net/v4_6_release/apis/3.0/company/companies/{companyID}"
    headers = {
        "Authorization": Auth,
        "ClientID": ClientID,
        "Content-Type": "application/json"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        return {"name": str(data["name"]), "phone": str(data["phoneNumber"])}
    except requests.RequestException as e:
        return "Unknown"

def getRecentTicket(phoneNumber):
    """
    Fetches the most recent ticket for a phone number.
    This is a BLOCKING function and MUST be called with run_in_executor.
    """
    if phoneNumber == "Unknown":
        return None
    

    if phoneNumber.startswith('1') and len(phoneNumber) == 11:
        phoneNumber = phoneNumber[1:]

    if len(phoneNumber) != 10:
        return '<small>Internal extension / Non-10-digit number.</small>'
        
    url_contact = f"https://api-na.myconnectwise.net/v4_6_release/apis/3.0/company/contacts?childconditions=communicationItems/value+like+{phoneNumber}"
    
    headers = {
        "Authorization": Auth,
        "ClientID": ClientID,
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url_contact, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if not data:
            return '<small>No contact found.</small>'
        
        contactID = str(data[0].get("id"))
        companyID = str(data[0].get("company", {}).get('id'))
        
    except requests.RequestException as e:
        logging.error(f"Error getting CW Contact for {phoneNumber}: {e}")
        return '<small>Error fetching contact.</small>'
    except IndexError:
        return None
        
    url_tickets = f"https://api-na.myconnectwise.net/v4_6_release/apis/3.0/service/tickets?conditions=contact/id={contactID}&orderBy=dateEntered+desc"
    
    try:
        response = requests.get(url_tickets, headers=headers, timeout=10)
        response.raise_for_status()
        tickets = response.json()
        if tickets:
            ticket_id = tickets[0]['id']
            summary = tickets[0]['summary']
            ticket_url = f"https://na.myconnectwise.net/v4_6_release/services/system_io/Service/fv_sr100_request.rails?service_recid={ticket_id}&companyName=capstone"
            
            output = f'<small><a href="{ticket_url}" target="_blank">#{ticket_id} - {summary}</a></small>'
            return output
        else:
            return '<small>No recent ticket.</small>' 
    except requests.RequestException as e:
        logging.error(f"Error getting CW Ticket for {contactID}: {e}")
        return '<small>Error fetching ticket.</small>' 


async def get_graph_api_token():
    auth_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    token_data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "https://graph.microsoft.com/.default",
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(auth_url, data=token_data)
        response.raise_for_status() 
        return response.json()["access_token"]


async def send_urgent_alert(caller_id, minutes, seconds, cid_name):
    logging.info(f"Attempting to send URGENT alert to group chat for {caller_id}...")
    
    teams4.title("Long Hold Time")
    teams4.text(f"Long hold time detected on {QR_QUEUE} queue for {caller_id}. Waiting for {minutes} minutes and {seconds} seconds.")
    manager.loop.run_in_executor(None, teams4.send)
    
    try:
        access_token = await get_graph_api_token()
    except Exception as e:
        teams4.title("Failed to Get Graph API Token")
        teams4.text(f"Failed to get Graph API token: {e}")
        manager.loop.run_in_executor(None, teams4.send)
        return

    caller_display = f"({cid_name}) {caller_id}" if cid_name != "Unknown" else caller_id
    
    adaptive_card_payload = {
        "type": "AdaptiveCard",
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "version": "1.5",
        "body": [
            {
                "type": "Container",
                "style": "attention",
                "items": [
                    {"type": "TextBlock", "text": "URGENT: LONG QUEUE WAIT TIME", "weight": "Bolder", "size": "Medium", "color": "Attention"}
                ]
            },
            {
                "type": "TextBlock", "text": f"A call from **{caller_display}** has been waiting for more than {minutes} minutes.", "wrap": True, "size": "Large"
            },
            {
                "type": "FactSet",
                "facts": [
                    {"title": "Caller ID:", "value": caller_id},
                    {"title": "Caller Name:", "value": cid_name},
                    {"title": "Current Wait:", "value": f"{minutes} minutes, {seconds} seconds"}
                ]
            },
            {
                "type": "TextBlock",
                "text": "Please ensure this call is addressed immediately.",
                "wrap": True
            }
        ]
    }
    
    graph_url = f"https://graph.microsoft.com/v1.0/chats/{CHAT_ID}/messages"
    
    message_payload = {
      "createdDateTime": datetime.now(timezone.utc).isoformat(),
      "from": {
          "user": {
              "id": SENDER_USER_ID,
              "displayName": SENDER_DISPLAY_NAME,
              "userIdentityType": "aadUser"
          }
      },
      "importance": "urgent",
      "body": {
        "contentType": "html",
        "content": "An urgent notification has been triggered for a long-waiting call."
      },
      "attachments": [{
          "contentType": "application/vnd.microsoft.card.adaptive",
          "content": json.dumps(adaptive_card_payload)
      }],
    }

    headers = { "Authorization": f"Bearer {access_token}" }

    async with httpx.AsyncClient() as client:
        try:
            teams4.title("Sending URGENT Alert")
            teams4.text(f"Sending URGENT alert for {caller_id} to group chat.")
            manager.loop.run_in_executor(None, teams4.send)
            
            response = await client.post(graph_url, headers=headers, json=message_payload)
            response.raise_for_status()
            
            teams4.text(f"Successfully sent URGENT alert for {caller_id} to the group chat.")
            manager.loop.run_in_executor(None, teams4.send)
            
        except httpx.HTTPStatusError as e:
            logging.error(f"ERROR sending Teams message: {e.response.status_code} - {e.response.text}")

async def send_email_async(html_body, plain_body):
    if not all([SMTP_SERVER, SMTP_SENDER_EMAIL, SENDER_PASSWORD, RECIPIENT_EMAILS]):
        logging.warning("Email configuration is incomplete. Skipping email.")
        return

    def email_sender_sync():
        try:
            msg = EmailMessage()
            msg['Subject'] = f"Daily Queue Report - {datetime.now().strftime('%Y-%m-%d')}"
            msg['From'] = SMTP_SENDER_EMAIL
            msg['To'] = RECIPIENT_EMAILS
            msg.set_content(plain_body)
            msg.add_alternative(html_body, subtype='html')
            logging.info("Email message created successfully.")

        except Exception as e:
            logging.error(f"Error creating the email message: {e}")
            return 

        server = None
        try:
            logging.info(f"Connecting to SMTP server at {SMTP_SERVER}:{SMTP_PORT}...")
            if SMTP_PORT == 465:
                logging.info("Establishing a direct SSL connection...")
                server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
            else:
                server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
                logging.info("Securing connection with STARTTLS...")
                server.starttls()
            logging.info("Connection established.")

            if SMTP_USER and SENDER_PASSWORD:
                logging.info(f"Logging in as {SMTP_USER}...")
                server.login(SMTP_USER, SENDER_PASSWORD)
                logging.info("Logged in successfully.")
            else:
                logging.info("Skipping login as no user or password was provided.")
            
            logging.info(f"Sending email to {RECIPIENT_EMAILS} from {SMTP_SENDER_EMAIL}...")
            server.send_message(msg)
            logging.info("✅ Email sent successfully!")

        except smtplib.SMTPAuthenticationError as e:
            logging.error(f"❌ Authentication failed for user {SMTP_USER}. Please check credentials. Server says: {e}")
        except ConnectionRefusedError:
            logging.error(f"❌ Connection refused. Is the SMTP server address '{SMTP_SERVER}' and port '{SMTP_PORT}' correct?")
        except smtplib.SMTPConnectError as e:
            logging.error(f"❌ Failed to connect to the server. Check server address, port, and firewall rules. Error: {e}")
        except Exception as e:
            logging.error(f"❌ An unexpected error occurred: {e}")
        finally:
            if server:
                logging.info("Closing connection.")
                server.quit()

    await manager.loop.run_in_executor(None, email_sender_sync)


async def check_queue_periodically():
    global alerted_calls
    alerted_calls = []
    while True:
        await asyncio.sleep(2) 
        
        try:
            queue_details = await manager.send_action(
                {'Action': 'QueueStatus', 'Queue': QR_QUEUE}
            )
        except Exception as e:
            logging.error(f"Error checking queue status: {e}")
            await asyncio.sleep(5)
            continue
            
        msg = "**Current Calls in Queue:**\n\n"
        found_calls = False
        longest_wait_time = 0
        current_calls_data = [] 
        current_queue_count = 0

        for event in queue_details:
            if event.Event == "QueueEntry": 
                found_calls = True
                current_queue_count += 1
                caller_id = event.get("CallerIDNum", "Unknown")
                
                wait_time_seconds = 0
                try:
                    wait_time_seconds = int(event.get("Wait", 0))
                except ValueError:
                    wait_time_seconds = 0 

                wait_time_minutes, wait_time_remaining_seconds = divmod(wait_time_seconds, 60)
                
                if wait_time_seconds > longest_wait_time:
                    longest_wait_time = wait_time_seconds
                
                call_info = call_map.get(event.get("Uniqueid", "N/A"), {})
                cid_name = call_info.get("caller_id", "Unknown")


                if cid_name == "Unknown":
                    try:
                        cid_name_from_api = await manager.loop.run_in_executor(None, getCID, caller_id)
                        if cid_name_from_api != "Unknown":
                             cid_name = cid_name_from_api
                    except Exception as e:
                        logging.error(f"Error fetching CID for {caller_id}: {e}")


                current_calls_data.append({
                    "id": event.get("Uniqueid", "N/A"),
                    "caller_id": caller_id,
                    "name": cid_name,
                    "wait_time": wait_time_seconds
                })
                

                if wait_time_minutes >= 4 and caller_id not in alerted_calls:
                    logging.info(f"Wait time for {caller_id} is {wait_time_minutes}m. Triggering urgent alert.")
                    await send_urgent_alert(caller_id, wait_time_minutes, wait_time_remaining_seconds, cid_name)
                    alerted_calls.append(caller_id)
        

        REAL_TIME_DATA["current_queue_count"] = current_queue_count
        REAL_TIME_DATA["longest_wait_time_seconds"] = longest_wait_time
        REAL_TIME_DATA["calls_in_queue"] = current_calls_data
        

        if longest_wait_time > 300:
            teams.color("FF0000")
        elif longest_wait_time > 0:
            teams.color("FFFF00")
        else:
            teams.color("00FF00")
            
        if found_calls:
            teams.title(f"P2 Queue Status")
            msg = "**Current Calls in Queue:**\n\n"
            for call in current_calls_data:
                minutes, seconds = divmod(call['wait_time'], 60)
                name_display = f"({call['name']})" if call['name'] != 'Unknown' and call['name'] != call['caller_id'] else ''
                msg += f"- Call from **{call['caller_id']}** {name_display} waiting for **{minutes}m {seconds}s.**\n"
            teams.text(msg.strip())
            manager.loop.run_in_executor(None, teams.send)

async def update_channel_states_periodically():
    """
    Continuously monitors CoreShowChannels to find live calls, tracking the transition
    from Parked to Answered to accurately log the new answering agent.
    """
    

    INTERNAL_MAIN_LINES = {"5122200208", "15122200208", "7377570786", "17377570786"}

    def extract_cid_base(channel_string):
        """
        Helper to extract the base extension/peer name from channel string.
        Includes support for SIP, Local, and PJSIP channel types.
        """

        return channel_string.split("-")[0].split("@")[0].replace("SIP/", "").replace("Local/", "").replace("PJSIP/", "")

    while True:
        await asyncio.sleep(2) 
        
        try:
            response = await manager.send_action({
                'Action': 'CoreShowChannels'
            })
        except Exception as e:
            logging.error(f"Error fetching CoreShowChannels: {e}")
            await asyncio.sleep(10)
            continue
            
        current_live_calls = []
        current_parked_calls = []
        
        channels = {}
        if not isinstance(response, list):
            response = [response]

        for msg in response:
            if msg.Event == 'CoreShowChannel':
                channels[msg.Channel] = msg

        processed_channels = set()
        current_unique_ids = set()

        for channel_id, msg in channels.items():
            try: 
                if channel_id in processed_channels:
                    continue

                bridged_channel_id = msg.get('BridgedChannel')
                

                if bridged_channel_id and bridged_channel_id in channels:
                    bridged_msg = channels[bridged_channel_id]
                    
                    processed_channels.add(channel_id)
                    processed_channels.add(bridged_channel_id)

                    cid1 = extract_cid_base(msg.Channel)
                    cid2 = extract_cid_base(bridged_msg.Channel)

                    is_msg_agent = cid1 in tech_dict
                    is_bridged_msg_agent = cid2 in tech_dict
                    
                    agent_msg = None
                    caller_msg = None
                    

                    if is_msg_agent and not is_bridged_msg_agent:
                        agent_msg = msg
                        caller_msg = bridged_msg
                    elif is_bridged_msg_agent and not is_msg_agent:
                        agent_msg = bridged_msg
                        caller_msg = msg
                        

                    elif is_msg_agent and is_bridged_msg_agent:
                        # If both CIDs are in tech_dict (e.g., 125 and 127 in your scenario),
                        # prioritize the SIP/PJSIP channel as the agent's live speaking channel.
                        if msg.Channel.startswith('SIP') or msg.Channel.startswith('PJSIP'):
                            agent_msg = msg
                            caller_msg = bridged_msg
                        elif bridged_msg.Channel.startswith('SIP') or bridged_msg.Channel.startswith('PJSIP'):
                            agent_msg = bridged_msg
                            caller_msg = msg
                        else:

                            continue 
                            
                    else:

                        continue 
                        

                    if caller_msg.get('Application') == 'Queue':
                        continue


                    agent_cid = extract_cid_base(agent_msg.Channel)
                    agent_name = tech_dict.get(agent_cid, f"Ext {agent_cid}") 
                    caller_uniqueid = caller_msg.get('Uniqueid')
                    current_unique_ids.add(caller_uniqueid)
                    
                    current_state = call_states.get(caller_uniqueid, {"status": "unknown", "agent": None})

                    if current_state["status"] == "parked" or current_state["agent"] != agent_name:
                        
                        if current_state["status"] == "parked":
                            
                            connected_line_num = agent_msg.get('ConnectedLineNum')
                            
                            if connected_line_num and extract_cid_base(connected_line_num) in tech_dict:
                                agent_name = tech_dict.get(extract_cid_base(connected_line_num), agent_name)
                            
                            logging.info(f"Call {caller_uniqueid} unparked and assigned to: {agent_name}")

                        call_states[caller_uniqueid] = {"status": "answered", "agent": agent_name}

                    if caller_uniqueid not in ANSWERED_CALL_START_TIMES:
                         ANSWERED_CALL_START_TIMES[caller_uniqueid] = datetime.now()
                         
                    caller_num = "Unknown"
                    
                    nums_to_check = [
                        caller_msg.get('CallerIDNum'),
                        caller_msg.get('ConnectedLineNum'),
                        agent_msg.get('ConnectedLineNum'),
                    ]
                    
                    for num in nums_to_check:
                        if num and len(num) > 8 and extract_cid_base(num) not in tech_dict and num not in INTERNAL_MAIN_LINES:
                            caller_num = num
                            break

                    caller_name = "Unknown"
                    if caller_uniqueid in call_map:
                         caller_name = call_map[caller_uniqueid].get('caller_id', 'Unknown')
                         if caller_num == "Unknown":
                              caller_num = call_map[caller_uniqueid].get('number', 'Unknown')
                              
                    if caller_name == "Unknown" and len(caller_num) >= 10:
                        try:
                            caller_name_from_cid = await manager.loop.run_in_executor(None, getCID, caller_num)
                            caller_name = caller_name_from_cid if caller_name_from_cid != "Unknown" else caller_num
                        except Exception:
                            caller_name = caller_num
                    else:
                        caller_name = caller_num if caller_num != "Unknown" else "Internal/Unknown Call"
                        
                    DurationStr = agent_msg.get("Duration", "00:00:00")
                    try:
                        parts = list(map(int, DurationStr.split(':')))
                        duration_sec = (parts[0] * 3600) + (parts[1] * 60) + parts[2]
                    except ValueError:
                        duration_sec = 0

                    recent_ticket_html = None
                    if caller_num not in ["Unknown", "Outbound Call"]:
                        now = datetime.now()
                        cache_entry = ACTIVE_CALL_CW_CACHE.get(caller_num)

                        if cache_entry and (now - cache_entry['timestamp']) < timedelta(minutes=10):
                            recent_ticket_html = cache_entry['ticket']
                        elif len(caller_num) >= 10: 
                            try:
                                recent_ticket_html = await manager.loop.run_in_executor(None, getRecentTicket, caller_num)
                                ACTIVE_CALL_CW_CACHE[caller_num] = {
                                    'ticket': recent_ticket_html,
                                    'timestamp': now
                                }
                            except Exception as e:
                                recent_ticket_html = "<small>Error fetching ticket.</small>"
                                ACTIVE_CALL_CW_CACHE[caller_num] = {
                                    'ticket': recent_ticket_html,
                                    'timestamp': now
                                }
                        else:
                            recent_ticket_html = "<small>Internal Call</small>"
                    else:
                        recent_ticket_html = "<small>Internal/Outbound Call</small>"


                    current_live_calls.append({
                        "agent_name": agent_name,
                        "caller_name": caller_name,
                        "duration_seconds": duration_sec,
                        "recent_ticket": recent_ticket_html 
                    })
                

                elif msg.get('Application') == 'Parked Call':
                    caller_uniqueid = msg.get('BridgedUniqueid') or msg.get('Uniqueid')
                    current_unique_ids.add(caller_uniqueid)
                    
                    caller_num = msg.get('CallerIDNum', 'Unknown')
                    DurationStr = msg.get("Duration", "00:00:00")

                    call_states[caller_uniqueid] = {"status": "parked", "agent": None}

                    try:
                        parts = list(map(int, DurationStr.split(':')))
                        duration_sec = (parts[0] * 3600) + (parts[1] * 60) + parts[2]
                            
                        caller_name_from_cid = await manager.loop.run_in_executor(None, getCID, caller_num)
                        caller_name = caller_name_from_cid if caller_name_from_cid != "Unknown" else caller_num

                        current_parked_calls.append({
                            "lot": "N/A", 
                            "caller_name": caller_name,
                            "caller_num": caller_num,
                            "duration_seconds": duration_sec
                        })
                    except Exception as e:
                        logging.error(f"Error processing parked call: {e}")
                        continue

            except Exception as channel_error:
                logging.error(f"Skipping channel {channel_id} due to processing error: {channel_error}")
                continue 

        keys_to_delete = [
            uid for uid in list(call_states.keys()) 
            if uid not in current_unique_ids and call_states[uid]["status"] != "waiting"
        ]
        for uid in keys_to_delete:
            del call_states[uid]
            
        REAL_TIME_DATA["live_active_calls"] = current_live_calls
        REAL_TIME_DATA["parked_calls"] = current_parked_calls
async def send_hourly_report():
  while True:
    if datetime.now().hour > QR_END_HOUR or datetime.now().hour < QR_START_HOUR:
      await asyncio.sleep(1800)
      continue
    if (datetime.now().weekday() >= 5):
      await asyncio.sleep(10000)
      continue
      
    now = datetime.now()
    seconds_to_next_hour = 3600 - (now.minute * 60 + now.second)
    await asyncio.sleep(seconds_to_next_hour)
    
    if len(hourly_wait_times) > 0:
      total_wait_time = sum(hourly_wait_times)
      average_wait_time = total_wait_time / len(hourly_wait_times)
      
      avg_minutes, avg_seconds = divmod(int(average_wait_time), 60)
      
      REAL_TIME_DATA["hourly_report"] = {
        "total_calls": len(hourly_wait_times),
        "avg_wait_time_seconds": average_wait_time,
        "calls_by_agent": dict(hourly_call_counts),
        "abandoned_calls": list(call_abandoned_hourly)
      }
      
      report_msg = (
        f"**Hourly Queue Report**\n\n"
        f"**Total Calls:** {len(hourly_wait_times)}\n\n"
        f"**Average Hold Time:** {avg_minutes} minutes and {avg_seconds:02d} seconds.\n"
      )
      
      teams2.title("Hourly Queue Report")
      teams2.text(report_msg)
      manager.loop.run_in_executor(None, teams2.send)

      hourly_wait_times.clear()
      hourly_call_counts.clear()
      call_abandoned_hourly.clear()
      
      teams4.title("Reset Daily Data")
      teams4.text("Cleared daily wait times and call counts for the next hour.")
      manager.loop.run_in_executor(None, teams4.send)
    else:
      teams2.title("Hourly Queue Report")
      teams2.text("No calls were received in the last hour.")
      manager.loop.run_in_executor(None, teams2.send)

async def send_daily_report():
  while True:
    if (datetime.now().hour >= QR_END_HOUR or datetime.now().hour < QR_START_HOUR) and datetime.now().weekday() < 5:
      
      seconds_to_next_day_start = ((24 - datetime.now().hour) + QR_START_HOUR) * 3600 - datetime.now().minute * 60 - datetime.now().second
      await asyncio.sleep(seconds_to_next_day_start)
      
      if len(daily_wait_times) > 0:
        total_wait_time = sum(daily_wait_times)
        average_wait_time = total_wait_time / len(daily_wait_times)
        
        avg_minutes, avg_seconds = divmod(int(average_wait_time), 60)
        
        REAL_TIME_DATA["daily_report"] = {
          "total_calls": len(daily_wait_times),
          "avg_wait_time_seconds": average_wait_time,
          "calls_by_agent": dict(daily_call_counts),
          "abandoned_calls": list(call_abandoned_count)
        }
        
        report_msg = (
          f"**Daily Queue Report**\n\n"
          f"**Total Calls:** {len(daily_wait_times)}\n\n"
          f"**Average Hold Time:** {avg_minutes} minutes and {avg_seconds:02d} seconds."
        )
        
        html_report_msg = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333333; line-height: 1.6;">
         <div style="max-width: 600px; margin: 20px auto; padding: 20px; border: 1px solid #dddddd; border-radius: 8px;">
          <h2 style="color: #005a9e; border-bottom: 2px solid #eeeeee; padding-bottom: 10px;">Daily Queue Report</h2>
          <p><strong>Total Calls:</strong> {len(daily_wait_times)}</p>
          <p><strong>Average Hold Time:</strong> {avg_minutes} minutes and {avg_seconds:02d} seconds.</p>
          <h3 style="color: #005a9e; margin-top: 30px;">Calls Answered by Agent:</h3>
          <ul style="list-style-type: none; padding-left: 0;">
        """

        for agent, count in daily_call_counts.items():
          html_report_msg += f'<li style="padding: 5px 0; border-bottom: 1px solid #f4f4f4;"><strong>{agent}</strong> answered <strong>{count}</strong> calls today.</li>'

        html_report_msg += """
          </ul>

          <h3 style="color: #005a9e; margin-top: 30px;">Abandoned Calls:</h3>
          <ul style="list-style-type: none; padding-left: 0;">
        """

        if call_abandoned_count:
          for abandoned_call in call_abandoned_count:
            html_report_msg += f'<li style="padding: 5px 0;">{abandoned_call.replace("*", "")}</li>'
        else:
          html_report_msg += '<li style="padding: 5px 0;">No abandoned calls today.</li>'

        html_report_msg += """
          </ul>
         </div>
        </body>
        </html>
        """

        teams2.title("Daily Queue Report")
        teams2.text(report_msg)
        manager.loop.run_in_executor(None, teams2.send)
        
        await send_email_async(html_body, report_msg)
        
        daily_wait_times.clear()
        call_abandoned_count.clear() 
        daily_call_counts.clear() 
        
        global daily_abandoned_call_objects
        daily_abandoned_call_objects = []
        
        teams4.title("Reset Daily Data")
        teams4.text("Cleared daily wait times and call counts for the next day.")
        manager.loop.run_in_executor(None, teams4.send)
        
      else:
        teams2.title("Daily Queue Report")
        teams2.text("No calls were received today.")
        manager.loop.run_in_executor(None, teams2.send)
    else:
      await asyncio.sleep(3600)
      

@manager.register_event("MessageWaiting")
async def Voicemail_Left(manager, message):
  await asyncio.sleep(2)
  teams4.text("Voicemail Left Event Fired")
  manager.loop.run_in_executor(None, teams4.send)

  caller_name = "Unknown"
  caller_number = "Unknown"

  if abandoned_call_namnum:
    last_entry_tuple = list(abandoned_call_namnum.items())[-1]
    caller_name = last_entry_tuple[0]
    caller_number = last_entry_tuple[1]
    abandoned_call_namnum.clear()

  teams.title("New Voicemail Received")
  teams.text(f"The caller **{caller_name} ({caller_number})** has left a **voicemail!**")
  manager.loop.run_in_executor(None, teams.send)

@manager.register_event("AgentConnect")
async def AgentConnect(manager, message):
  call_id = message.get("Uniqueid")
  agent_name = message.MemberName if message.MemberName else "Unknown"
  agent_name = str(agent_name)
  if call_id and call_id in call_states:
    call_states[call_id] = {"status": "answered", "agent": agent_name}
    
    ANSWERED_CALL_START_TIMES[call_id] = datetime.now()
    
    daily_call_counts[agent_name] = daily_call_counts.get(agent_name, 0) + 1
    hourly_call_counts[agent_name] = hourly_call_counts.get(agent_name, 0) + 1
    logging.info(daily_call_counts)
    teams4.title("Agent Connect Event Fired")
    teams4.text(f"Call {call_id} was answered by {agent_name}. Call counts incremented.")
    manager.loop.run_in_executor(None, teams4.send)
    

@manager.register_event("QueueMemberAdded")
async def QueueAdd(manager, message):
  if message["Queue"] != QR_QUEUE:
    return
  queue_details = await manager.send_action(
    {'Action': 'QueueStatus', 'Queue': QR_QUEUE}
  )
  members = list(filter(lambda x: "Name" in x, queue_details))
  teams3.title("QR Join")
  teams3.text("{} has logged in to QR.".format(message["MemberName"]))
  manager.loop.run_in_executor(None, teams3.send)
  msg = ""
  for member in members:
    msg += "- {} is in QR.\n".format(member["Name"])
  if len(members) >= 2:
    triage_member = members[1]["Name"]
  elif len(members) == 1:
    triage_member = members[0]["Name"]
  else:
    triage_member = "No one"
  msg += "\n<b>{}</b> is responsible for triage.".format(triage_member)
  teams3.title("QR List")
  teams3.text(msg.strip())
  manager.loop.run_in_executor(None, teams3.send)

@manager.register_event("CDR")
async def CDR(manager, message):
  teams4.text("CDR Event Fired")
  manager.loop.run_in_executor(None, teams4.send)
  teams4.text("I'm fairly certain this event will never fire as it doesn't exist in the current Asterisk version. If it does this code needs to be remoade as there's a batter way to do this now.")
  manager.loop.run_in_executor(None, teams4.send)


@manager.register_event("Leave")
async def CallLeave(manager, message):
  if message["Queue"] != QR_QUEUE:
    return
  
  call_id = message.get("Uniqueid")
  await asyncio.sleep(1.5) 
  logging.info(f"{call_map[call_id] if call_id in call_map else 'No call data found for this Call ID.'}")
  abandoned_caller_data = call_map.pop(call_id, {"caller_id": "Unknown", "number": "Unknown", "raw_number": "Unknown"})
  caller_id = abandoned_caller_data["caller_id"]
  phone_number = abandoned_caller_data["number"]
  
  logging.info(f"Processing CallLeave for Call ID: {call_id}, Caller ID: {caller_id}, Phone Number: {phone_number}")
  raw_caller_num = message.get("CallerIDNum", "Unknown")
  raw_number_from_map = abandoned_caller_data.get("raw_number", "Unknown")
  logging.info(f"Raw Caller Number from Message: {raw_caller_num}")
    
  if caller_id == "Unknown" and (phone_number == "Unknown" or phone_number == ""):
    final_number = raw_number_from_map if raw_number_from_map != "Unknown" else raw_caller_num
        
    if final_number != "Unknown":
      phone_number = final_number
      caller_id = phone_number # Use the phone number as the temporary ID/name
    
  logging.info(f"Final Caller ID: {caller_id}, Phone Number: {phone_number}")
  wait_duration = datetime.now() - call_join_times.pop(call_id, datetime.now())
  wait_time_seconds = wait_duration.total_seconds()
  hourly_wait_times.append(wait_time_seconds)
  daily_wait_times.append(wait_time_seconds)

  answered_by = "Abandoned"

  if call_id in call_states and call_states[call_id]["status"] == "answered":
    agent_name = call_states[call_id]["agent"]
    reason = f"was **answered by {agent_name}**"
    answered_by = agent_name
    abandoned = False
  else:
    reason = " was **abandoned**"
    abandoned = True
    
    call_abandoned_hourly.append(f"Call from **{caller_id} ({phone_number})** was abandoned after waiting {int(wait_time_seconds)} seconds.")
    call_abandoned_count.append(f"Call from **{caller_id} ({phone_number})** was abandoned after waiting {int(wait_time_seconds)} seconds.")
    
    current_time_cst = datetime.now(timezone(timedelta(hours=-6))) 
    
    abandoned_call_data = {
      "name": caller_id,
      "number": phone_number,
      "time": current_time_cst.strftime("%I:%M:%S %p"),
      "wait_time": int(wait_time_seconds)
    }
    daily_abandoned_call_objects.append(abandoned_call_data)
    
    if call_id in call_states:
      try:
        del call_states[call_id]
      except KeyError:
        pass
    
  queue_count = message.get("Count", 0)
  wait_time_minutes, wait_time_remaining_seconds = divmod(int(wait_duration.total_seconds()), 60)
  
  teams.title("Call Left Queue")
  teams.color("00FF00" if not abandoned else "FF0000") # Green if answered, Red if abandoned
  

  display_id = caller_id if caller_id != "Unknown" else phone_number

  teams.text(
    f"A call from **{display_id}** {reason}. "
    f"There are now **{queue_count}** calls in queue. "
    f"The total hold time was **{wait_time_minutes}** minutes and **{wait_time_remaining_seconds}** seconds."
  )
  manager.loop.run_in_executor(None, teams.send)
  
  teams4.title("Call Left Queue")
  teams4.text(f"Call {call_id} from {caller_id} has left the queue after waiting {wait_time_minutes} minutes and {wait_time_remaining_seconds} seconds. Answered by: {answered_by}")
  manager.loop.run_in_executor(None, teams4.send)
  
  daily_call_log.append({
    "timestamp": datetime.now().isoformat(),
    "call_id": call_id,
    "agent": answered_by,
    "caller_id": caller_id,
    "caller_number": phone_number
  })

@manager.register_event("Hangup")
async def Hangup(manager, message):
  call_id = message.get("Uniqueid")
  
  if call_id in ANSWERED_CALL_START_TIMES:
    start_time = ANSWERED_CALL_START_TIMES.pop(call_id)
    duration = (datetime.now() - start_time).total_seconds()
    
    if call_id in call_states and call_states[call_id]["status"] == "answered":
      agent_name = call_states[call_id]["agent"]
      
      AGENT_TOTAL_TALK_TIME[agent_name] = AGENT_TOTAL_TALK_TIME.get(agent_name, 0) + duration
      daily_call_counts[agent_name] = daily_call_counts.get(agent_name, 0) + 1
      hourly_call_counts[agent_name] = hourly_call_counts.get(agent_name, 0) + 1
      logging.info(f"Logged {duration}s talk time for {agent_name}. Call count incremented.")
  
  await asyncio.sleep(2)
      
  if call_id in call_states:
    try:
      del call_states[call_id]
    except KeyError:
      pass
  

  logging.info(f"Hangup processing for Call ID: {call_map[call_id] if call_id in call_map else 'No call data found for this Call ID.'}")
  if call_id in call_map:
    try:
      del call_map[call_id]
      logging.info(f"Cleaned up call_map for hung-up call: {call_id}")
    except KeyError:
      pass
  

@manager.register_event("Join")
async def CallJoin(manager, message):
  if message["Queue"] != QR_QUEUE:
    return
  
  teams4.text(f"Join Event Fired: {message}")
  manager.loop.run_in_executor(None, teams4.send)
  
  call_id = message.get("Uniqueid")
  if call_id:
    call_join_times[call_id] = datetime.now()
  try:
    caller_id = message["CallerIDNum"]
  except KeyError:
    caller_id = "Unknown"
    
  raw_caller_id_from_ami = message.get("CallerIDNum", "Unknown")
  logging.info(raw_caller_id_from_ami)
  if call_id:
    call_states[call_id] = {"status": "waiting", "agent": None}
  
  
  is_external_number = False
  
  if caller_id.startswith('1') and len(caller_id) == 11:
    caller_id = caller_id[1:] # Strip '1', now 10 digits
    is_external_number = True
  elif len(caller_id) == 10:
    is_external_number = True
  
  callName = "Unknown"
  notcomp = True
  
  if caller_id != "Unknown" and is_external_number:
    try:
      callName = await manager.loop.run_in_executor(None, getCID, caller_id)
    except Exception:
      pass

    company_id = await manager.loop.run_in_executor(None, getCompanyID, caller_id)
    
    if company_id != "Unknown":
      company_info = await manager.loop.run_in_executor(None, getCompanyNumber, company_id)
      
      teams4.text(f"Got company info for {caller_id}")
      manager.loop.run_in_executor(None, teams4.send)
      
      if company_info != "Unknown":
        if str(company_info["phone"]) == str(caller_id):
          callName = company_info["name"]
          notcomp = False
  
  teams4.text(f"Call {call_id} from {caller_id} has joined the queue.")
  manager.loop.run_in_executor(None, teams4.send)
  
  queue_count = message["Count"]
  teams.title("Call in Queue")
  msg = (f"A call from **{callName}** **{caller_id}** has entered the queue. There are now **{queue_count}** calls in queue.")
  
  if notcomp and is_external_number:
    recent_ticket = await manager.loop.run_in_executor(None, getRecentTicket, caller_id)
    if recent_ticket and "No recent ticket" not in recent_ticket and "Error" not in recent_ticket:
      msg += (f"\n\n\n\nCaller has a recent ticket.")
  elif not notcomp:
    pass 
  else:
    teams4.text(f"Skipping recent ticket check for internal number: {caller_id}")
    manager.loop.run_in_executor(None, teams4.send)
    
  teams.text(msg)
  teams.color("00FF00") 
  manager.loop.run_in_executor(None, teams.send)
  logging.info(caller_id)
  logging.info(raw_caller_id_from_ami)
  call_map[call_id] = {
        "caller_id" : callName, 
        "number" : caller_id,
        "raw_number": raw_caller_id_from_ami # <-- New field saved here
    }
  
  queue_details = await manager.send_action(
    {'Action': 'QueueStatus', 'Queue': QR_QUEUE}
  )


@manager.register_event("QueueMemberRemoved")
async def QueueLeave(manager, message):
  if message["Queue"] != QR_QUEUE:
    return
  queue_details = await manager.send_action(
    {'Action': 'QueueStatus', 'Queue': QR_QUEUE}
  )
  members = list(filter(lambda x: "Name" in x, queue_details))
  teams3.title("QR Leave")
  teams3.text("{} has logged out of QR.".format(message["MemberName"]))
  manager.loop.run_in_executor(None, teams3.send)
  queue_summary = await manager.send_action(
    {'Action': 'QueueSummary', 'Queue': QR_QUEUE}
  )
  if int(queue_summary[1]["LoggedIn"]) == 0:
    teams3.title("QR Empty")
    teams3.text("**QR is empty!**")
    manager.loop.run_in_executor(None, teams3.send)
  else:
    msg = ""
    for member in members:
      msg += "- {} is in QR.\n".format(member["Name"])
    if len(members) >= 2:
      triage_member = members[1]["Name"]
    elif len(members) == 1:
      triage_member = members[0]["Name"]
    else:
      triage_member = "No one"
    msg += "\n<b>{}</b> is responsible for triage.".format(triage_member)
    teams3.title("QR List")
    teams3.text(msg.strip())
    manager.loop.run_in_executor(None, teams3.send)


@manager.register_event("Voicemail")
async def Voicemail_Left(manager, message):
  response = await manager.send_action({
        'Action': 'MailboxStatus',
        'Mailbox': '199@default'
      })
  logging.info(response)
  logging.info(message)


async def logCurrentQueueinfo():
  while True:
    now = datetime.now()
    if now.hour >= QR_START_HOUR and now.hour < QR_END_HOUR:
      seconds_to_next_hour = 3600 - (now.minute * 60 + now.second)
      await asyncio.sleep(seconds_to_next_hour)
    else:
      await asyncio.sleep(3600)
    msg = "**Hourly Queue Info Log:**\n\n"
    if len(daily_call_counts) != 0:
      for x, count in daily_call_counts.items():
        msg += f"{x}: {count}\n\n"
    teams4.title("Hourly Queue Info Log")
    teams4.text(msg.strip())
    manager.loop.run_in_executor(None, teams4.send)


async def resetDailyQueueinfo():
  while True:
    if datetime.now().hour == 0:
      daily_wait_times.clear()
      call_abandoned_count.clear() 
      daily_call_counts.clear()
      AGENT_TOTAL_TALK_TIME.clear()
      ANSWERED_CALL_START_TIMES.clear()
      REAL_TIME_DATA["daily_report"]["abandoned_call_details"] = []
      REAL_TIME_DATA["call_log"] = []
      daily_abandoned_call_objects.clear()
      daily_call_log.clear()
      
      
      
      teams4.title("Reset Daily Data")
      teams4.text("Cleared daily wait times and call counts for the next day.")
      manager.loop.run_in_executor(None, teams4.send)
      
    await asyncio.sleep(3600) 

async def update_daily_stats_periodically():
  while True:
    await asyncio.sleep(5) 

    if len(daily_wait_times) > 0:
      total_wait_time = sum(daily_wait_times)
      average_wait_time = total_wait_time / len(daily_wait_times)
    else:
      total_wait_time = 0
      average_wait_time = 0
      
    agent_avg_talk_time = {}
    total_calls_by_agent = dict(daily_call_counts) 
      
    for agent_name, call_count in total_calls_by_agent.items():
      total_time = AGENT_TOTAL_TALK_TIME.get(agent_name, 0)
      avg_time = total_time / call_count if call_count > 0 else 0
      agent_avg_talk_time[agent_name] = avg_time
      
    REAL_TIME_DATA["daily_report"] = {
      "total_calls": len(daily_wait_times) - len(call_abandoned_count),
      "avg_wait_time_seconds": average_wait_time,
      "abandoned_calls_count": len(call_abandoned_count),
      "calls_by_agent": total_calls_by_agent,
      "abandoned_call_details": list(daily_abandoned_call_objects),
      "agent_avg_talk_time": agent_avg_talk_time 
    }
    
    if len(hourly_wait_times) > 0:
      total_wait_time_hourly = sum(hourly_wait_times)
      average_wait_time_hourly = total_wait_time_hourly / len(hourly_wait_times)
    else:
      average_wait_time_hourly = 0
      
    REAL_TIME_DATA["hourly_report"] = {
      "total_calls": len(hourly_wait_times),
      "avg_wait_time_seconds": average_wait_time_hourly,
      "calls_by_agent": dict(hourly_call_counts),
      "abandoned_calls": list(call_abandoned_hourly),
    }
    REAL_TIME_DATA["call_log"] = list(daily_call_log)
    



@app.route("/")
def index():
  """Serves the main HTML dashboard."""
  return render_template("index.html")

@app.route('/stream')
def stream():
  """Server-Sent Events (SSE) endpoint to push real-time data to the browser."""
  def generate():
    while True:
      try:
        data_dump = json.dumps(REAL_TIME_DATA)
        yield f"data:{data_dump}\n\n"
        time.sleep(1)
      except (GeneratorExit, Exception) as e:
            logging.info(f"SSE Client disconnected or error: {e}")
            break

  return Response(generate(), mimetype="text/event-stream")




def run_asterisk_manager_loop():
  """Starts the Asterisk manager connection and runs its asyncio loop."""
  teams4.title("Asterisk Manager Service Started")
  teams4.text("The Asterisk manager monitoring service has started successfully.")
  manager.loop.run_in_executor(None, teams4.send)
  
  manager.connect()
  

  asyncio.ensure_future(check_queue_periodically(), loop=manager.loop)
  asyncio.ensure_future(update_channel_states_periodically(), loop=manager.loop)
  asyncio.ensure_future(send_hourly_report(), loop=manager.loop)
  asyncio.ensure_future(send_daily_report(), loop=manager.loop)
  asyncio.ensure_future(resetDailyQueueinfo(), loop=manager.loop)
  asyncio.ensure_future(logCurrentQueueinfo(), loop=manager.loop)
  asyncio.ensure_future(update_daily_stats_periodically(), loop=manager.loop)
  try:
    manager.loop.run_forever()
  except KeyboardInterrupt:
    manager.loop.close()
    
    
@app.route("/health")
def health_check():
  if manager.authenticated:
    return "OK", 200
  else:
    return "Service Unavailable", 503

def main():
  try:
    teams4.title("QR Web Service Initializing")
    teams4.text("Starting Asterisk Manager in background thread and Flask web server.")
    teams4.send() 
  except Exception as e:
    logging.warning(f"WARNING: Initial Teams log failed (this is non-critical): {e}")
  
  threading.Thread(target=run_asterisk_manager_loop, daemon=True).start()

  if os.getenv("DEBUG_MODE") == "true":
    app.run(host='0.0.0.0', port=5000, debug=True)

  time.sleep(30)
  logging.info(f"PBX IP: {HOST}")
  logging.info(f"Using Connectwise Auth: {Auth[:10]}...[REDACTED]")
  logging.info(f"Using Connectwise Client ID: {ClientID}")

gunicorn_logger = logging.getLogger('gunicorn.error')
app.logger.handlers = gunicorn_logger.handlers
app.logger.setLevel(gunicorn_logger.level)

main()

if __name__ == "__main__":
  pass
