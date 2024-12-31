from websockets.sync.client import connect
from threading import Thread, Event
import requests
import asyncio
import json
import urllib
import webbrowser
import os
import time
from utils.logging import create_sys_logger
from utils.observer import ObserverServer

'''
Class for interfacing with Twitch to track chat history and stream events using websockets
For reference: https://dev.twitch.tv/docs/eventsub/

We get user app tokens using OAuth code grant flow: https://dev.twitch.tv/docs/authentication/getting-tokens-oauth/#authorization-code-grant-flow

Usage:
- FOR CHAT HISTORY: call self.get_chat_history()
- FOR TWITCH EVENTS: subscribe to ObserverServer self.broadcast_server and listen for event "twitch_event"
'''
class TwitchContextMonitor():
    CLIENT_ID = os.getenv("TWITCH_APP_ID")
    CLIENT_SECRET = os.getenv("TWITCH_APP_TOKEN")
    OAUTH_REDIRECT_CODE = "http://localhost:5000/auth/redirect/code" # Needs to be added on Twitch Dev Console as well
    OAUTH_REDIRECT_TOKENS = "http://localhost:5000/auth/redirect/tokens" # Needs to be added on Twitch Dev Console as well
    OAUTH_TOKEN_URL = "https://id.twitch.tv/oauth2/token"
    OAUTH_AUTHORIZE_URL = "https://id.twitch.tv/oauth2/authorize?{}".format(urllib.parse.urlencode({
        "client_id": CLIENT_ID,
        "redirect_uri": OAUTH_REDIRECT_CODE,
        "response_type": "code",
        "scope": "user:read:chat" # https://dev.twitch.tv/docs/authentication/scopes/
    }))
    logger = create_sys_logger("twitch")

    # List of events:
    #   twitch_event: Triggered when a new twitch event occurs
    broadcast_server = ObserverServer()

    def __init__(self, jaison):
        self.jaison = jaison
        self.TOKEN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), f'twitch_api_tokens_{self.jaison.config.twitch_user_id}.json')
        self.broadcaster_id = self.jaison.config.twitch_broadcaster_id
        self.user_id = self.jaison.config.twitch_user_id
        self.access_token = None
        self.refresh_token = None
        self._load_tokens()

        self.event_ws = None

        self.chat_history = []
        self.event_thread = Thread(target=self._event_loop)
        self.event_thread.start()

    # Loads tokens from file if it exists
    # If token file does not exist or is not formatted correctly, then logs an error and does nothing else
    # Never fails, only returns status of successful load
    def _load_tokens(self) -> bool:
        try:
            with open(self.TOKEN_FILE, 'r') as f:
                token_o = json.load(f)
                self.access_token = token_o['access_token']
                self.refresh_token = token_o['refresh_token']
            return True
        except:
            self.logger.error("{} is missing or malformed. Needs to be reauthenticated at {}".format(self.TOKEN_FILE,self.OAUTH_AUTHORIZE_URL))
            return False

    # Use loaded refresh token to save a new access/refresh token pair
    def _refresh_tokens(self):
        response = requests.post(
            self.OAUTH_TOKEN_URL,
            params={
                "client_id": self.CLIENT_ID,
                "client_secret": self.CLIENT_SECRET,
                "refresh_token": self.refresh_token,
                "grant_type": 'refresh_token',
            }
        ).json()
        self.set_tokens(response['access_token'], response['refresh_token'])

    # Uses code (from webui) to save a new access/refresh token pair
    def set_tokens_from_code(self, code):
        response = requests.post(
            self.OAUTH_TOKEN_URL,
            params={
                "client_id": self.CLIENT_ID,
                "client_secret": self.CLIENT_SECRET,
                "code": code,
                "grant_type": 'authorization_code',
                "redirect_uri": self.OAUTH_REDIRECT_TOKENS
            }
        ).json()
        self.set_tokens(response['access_token'], response['refresh_token'])

    # Saves new access/refresh token pair to file and reloads from that file
    def set_tokens(self, access_token, refresh_token):
        with open(self.TOKEN_FILE, 'w') as f:
            json.dump({
                "access_token": access_token,
                "refresh_token": refresh_token
            }, f, indent=4)

        self._load_tokens()
        
    # Attempts subscription using Twitch Events Sub API
    # For reference: https://dev.twitch.tv/docs/eventsub/eventsub-subscription-types/
    def _subscribe(self):
        if self.access_token is None:
            self.logger.warning("Can't subscribe to events until authenticated. Please authenticate at {}".format(self.OAUTH_AUTHORIZE_URL))
            raise Exception("Can't complete subscription")

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Client-Id": self.CLIENT_ID,
            "Content-Type": "application/json"
        }
        self.logger.debug(f"Attemption subscription using headers: {headers}")
        for data in self.event_sub_data:
            self.logger.debug(f"Attempting subscription for: {data}")
            response = requests.post(
                'https://api.twitch.tv/helix/eventsub/subscriptions',
                headers=headers,
                json=data
            )
            if response.status_code == 401: # In case forbidden, refresh tokens and retry once
                self._refresh_tokens()
                headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Client-Id": self.CLIENT_ID,
                    "Content-Type": "application/json"
                }
                response = requests.post(
                    'https://api.twitch.tv/helix/eventsub/subscriptions',
                    headers=headers,
                    json=data
                )

            if response.status_code != 202: # If not successful, signal failure
                self.logger.warning(f"Failing to subscribe to event: {response.json()}")
                raise Exception("Can't complete subscription")
            

    # Connect a new socket and resubscribe to events on its new session
    def _setup_socket(self, reconnect_url: str = None):
        try:
            new_ws = connect(reconnect_url or "wss://eventsub.wss.twitch.tv/ws?keepalive_timeout_seconds=10")
            welcome_msg = json.loads(new_ws.recv())
            if self.event_ws:
                self.event_ws.close()
            self.event_ws = new_ws
            self.logger.debug(f'Connected new subscription events websocket: {welcome_msg}')
            self.session_id = welcome_msg['payload']['session']['id']
            
            # List of subscriptables: https://dev.twitch.tv/docs/eventsub/eventsub-subscription-types/#subscription-types
            self.event_sub_data = [
                {
                    "type": "channel.chat.notification",
                    "version": "1",
                    "condition": {
                        "broadcaster_user_id": self.broadcaster_id,
                        "user_id": self.user_id
                    },
                    "transport": {
                        "method": "websocket",
                        "session_id": self.session_id
                    }
                },
                {
                    "type": "channel.chat.message",
                    "version": "1",
                    "condition": {
                        "broadcaster_user_id": self.broadcaster_id,
                        "user_id": self.user_id
                    },
                    "transport": {
                        "method": "websocket",
                        "session_id": self.session_id
                    }
                }
            ]

            self._subscribe()
            return True
        except Exception as err:
            self.logger.error("Failed to setup Twitch subscribed events websocket: {}".format(err))
            return False

    # Wrapper for self._setup_socket to reattempt until success, retrying after delay on failure
    def setup_socket(self, reconnect_url: str = None):
        while True:
            self.logger.debug("Attempting to setup Twitch subscribed events websocket...")
            if self._setup_socket(reconnect_url=reconnect_url):
                break
            time.sleep(5)

    # Main event loop for handling incoming events from Twitch
    def _event_loop(self):
        self.logger.debug("Started event loop!")
        self.setup_socket()
        while True:
            try:
                event = json.loads(self.event_ws.recv())
                self.logger.debug("Event loop received event: {}".format(event))
                if 'metadata' not in event or 'payload' not in event: # Expect message to have a specific structure
                    self.logger.warning("Unexpected event: {}".format(event))
                    continue
                if event['metadata']['message_type'] == "notification": # Handling subscribed events
                    event = event['payload']
                    if 'subscription' in event and event['subscription']['type'] == 'channel.chat.notification': # Twitch Stream Events
                        self.broadcast_server.broadcast_event("twitch_event", payload={"event": event['event']['system_message']})
                    elif 'subscription' in event and event['subscription']['type'] == 'channel.chat.message': # Twitch Stream Chat Messages
                        self.chat_history.append({
                            "name": event['event']['chatter_user_name'],
                            "message": event['event']['message']['text']
                        })
                        self.chat_history = self.chat_history[-10:]
                elif event['metadata']['message_type'] == "session_reconnect": # Handling reconnect request
                    self.setup_socket(event['payload']['session']['reconnect_url'])
                elif event['metadata']['message_type'] == "revocation": # Notified of a subscription being removed by Twitch
                    self.logger.warning("A Twitch event subscrption has been revoked: {}".format(event['payload']['subscription']['type']))
            except Exception as err:
                # Event must continue to run even in event of error
                self.logger.error(f"Event loop ran into an error: {err}")

    # Used to get chat history
    def get_chat_history(self):
        return self.chat_history