from transformers import pipeline
from websockets.sync.client import connect
import json
import random
import os
import asyncio
from threading import Thread, Event
import time
from config import config
import copy
import time

# Make sure VTube Studio is running API is enabled to port 8001
class VTSHotkeyPlugin():
    def __init__(self):
        # Set configurables
        self.classifier = pipeline(task="text-classification", model="SamLowe/roberta-base-go_emotions", top_k=1, device='cuda')
        self.main_plugin_info = {
            "pluginName": "J.A.I.son Hotkeyer",
            "pluginDeveloper": "Limit Cant Code",
        }
        self.event_plugin_info = {
            "pluginName": "J.A.I.son Event Manager",
            "pluginDeveloper": "Limit Cant Code",
        }

        self.emotion_map = {}
        self.hotkey_map = {}
        self.animations = []
        self.DEFAULT_HOTKEY_SET = None
        self.hotkey_queue = []
        self.main_ws = self._setup_ws('vts_token_main.txt', self.main_plugin_info)
        self.event_ws = self._setup_ws('vts_token_events.txt', self.event_plugin_info)
        
        self._parse_hotkeys()

        self._trigger_hotkey_event = Event()
        self.event_listener_thread = Thread(target=self._event_listener)
        self.hotkey_thread = Thread(target=self._hotkey_exec_loop)
        self.event_listener_thread.start()
        self.hotkey_thread.start()

    # Setup and authenticate websocket to talk to VTube Studio instance API
    def _setup_ws(self, token_file: str, plugin_info: dict):
        try:
            # Connect to VTS API
            ws = connect(config['vts_api_address'])

            # Authenticate this Plugin
            auth_token = None
            if os.path.isfile(token_file): # Get token from file if gotten and saved previously
                token_file = open(token_file, 'r')
                auth_token = token_file.read()
                token_file.close()
                request = {
                    "apiName": "VTubeStudioPublicAPI",
                    "apiVersion": "1.0",
                    "requestID": "authenticate-plugin",
                    "messageType": "AuthenticationRequest",
                    "data": {
                        **plugin_info,
                        "authenticationToken": auth_token
                    }
                }
                ws.send(json.dumps(request))
                response = json.loads(ws.recv())
                if response['data']['authenticated']:
                    return ws
            
            # If no token file or authentication with saved token fails, reauthenticate
            # Authentication request (must accept on VTS GUI)
            request = {
                "apiName": "VTubeStudioPublicAPI",
                "apiVersion": "1.0",
                "requestID": "get-auth-token",
                "messageType": "AuthenticationTokenRequest",
                "data": plugin_info
            }
            ws.send(json.dumps(request))
            response = json.loads(ws.recv())
            if 'authenticationToken' in response['data']: # Save to file
                auth_token = response['data']['authenticationToken']
                token_file = open(token_file, 'w')
                token_file.write(auth_token)
                token_file.close()
            else:
                raise Exception("Did not get authenication token: {}".format(response))

            # Authenticate with new token
            request = {
                "apiName": "VTubeStudioPublicAPI",
                "apiVersion": "1.0",
                "requestID": "authenticate-plugin",
                "messageType": "AuthenticationRequest",
                "data": {
                    **plugin_info,
                    "authenticationToken": auth_token
                }
            }
            ws.send(json.dumps(request))
            response = json.loads(ws.recv())
            if not response['data']['authenticated']:
                raise Exception('Failed to authenticate VTS plugin: {}'.format(response))
            
            print("{} connected to API {}!".format(plugin_info['pluginName'], config['vts_api_address']))
            return ws
        except Exception as err:
            print(err)
            raise err

    # Parse configured hotkeys configuration for use by this plugin
    def _parse_hotkeys(self):
        # Info for debugging
        POSSIBLE_EMOTION_LABELS = set(["admiration","amusement","approval","caring","desire","excitement","gratitude","joy","love","optimism","pride","anger","annoyance","disappointment","disapproval","embarrassment","fear","disgust","grief","nervousness","remorse","sadness","confusion","curiosity","realization","relief","surprise","neutral"])
        vts_info = self._get_vts_info()
        POSSIBLE_HOTKEYS = set([hotkey[0] for hotkey in vts_info["hotkeys"]])
        self.animations = [hotkey[0] for hotkey in vts_info["hotkeys"] if hotkey[1]]

        # Config checks
        if 'vts_hotkey_config_file' not in config:
            raise Exception('"vts_hotkey_config_file" no configured...')
        elif not os.path.isfile(config['vts_hotkey_config_file']):
            raise Exception('Configured "vts_hotkey_config_file": "{}" does not exist'.format(config['vts_hotkey_config_file']))
        elif not config['vts_hotkey_config_file'].lower().endswith('.json'):
            raise Exception('Configured "vts_hotkey_config_file": "{}" is not a json'.format(config['vts_hotkey_config_file']))
        
        # Load and parse
        with open(config['vts_hotkey_config_file'], 'r') as hotkey_file:
            hotkey_dict = json.load(hotkey_file)
        unseen_emotions = copy.copy(POSSIBLE_EMOTION_LABELS)
        unseen_hotkeys = copy.copy(POSSIBLE_HOTKEYS)
        nonexist_emotions = set()
        nonexist_hotkeys = set()
        for hotkey_set in hotkey_dict:
            # Add to object map attributes
            self.emotion_map[hotkey_set] = hotkey_dict[hotkey_set]['emotions']
            self.hotkey_map[hotkey_set] = hotkey_dict[hotkey_set]['hotkeys']

            # set default set for idle
            if self.DEFAULT_HOTKEY_SET is None:
                self.DEFAULT_HOTKEY_SET = hotkey_set

            # Tracking unused and non-existing for preemptive debugging
            unseen_emotions = unseen_emotions - set(hotkey_dict[hotkey_set]['emotions'])
            unseen_hotkeys = unseen_hotkeys - set(hotkey_dict[hotkey_set]['hotkeys'])
            nonexist_emotions = nonexist_emotions | set(hotkey_dict[hotkey_set]['emotions']) - POSSIBLE_EMOTION_LABELS
            nonexist_hotkeys = nonexist_hotkeys | set(hotkey_dict[hotkey_set]['hotkeys']) - POSSIBLE_HOTKEYS

        # Show potentiall missing or mistyped emotions and hotkeys
        print("Finished parsing Hotkeys for VTS Plugin!")
        print("{} ({}) {}".format(vts_info['model_name'], vts_info['model_id'], 'is ready!' if vts_info['model_ready'] else 'is not ready...'))
        print("Emotions not assigned:   {}".format(unseen_emotions))
        print("Hotkeys not assigned:   {}".format(unseen_hotkeys))
        print("Emotions not found:   {}".format(nonexist_emotions))
        print("Hotkeys not found:   {}".format(nonexist_hotkeys))

    # Get general info from VTS
    def _get_vts_info(self):
        try:
            request = {
                "apiName": "VTubeStudioPublicAPI",
                "apiVersion": "1.0",
                "requestID": "SomeID",
                "messageType": "HotkeysInCurrentModelRequest",
                "data": {}
            }

            self.main_ws.send(json.dumps(request))
            response = json.loads(self.main_ws.recv())
            output = {
                "model_ready": response['data']['modelLoaded'],
                "model_name": response['data']['modelName'],
                "model_id": response['data']['modelID'],
                "hotkeys": [(hotkey_obj['name'], hotkey_obj['type'] == "TriggerAnimation") for hotkey_obj in response['data']['availableHotkeys']], # hotkey[1] is True when hotkey triggers an animation
            }
        except Exception as err:
            print("VTS Plugin failed to get VTS info")
            print(err)
            raise err

        return output

    # Event listener that runs in a separate thread
    # Waits for currently playing animation to end (not overwritten by another animation)
    # Then triggers next hotkey to be pressed
    def _event_listener(self):
        # Subscribe to hotkey end event
        try:
            request = json.dumps({
                "apiName": "VTubeStudioPublicAPI",
                "apiVersion": "1.0",
                "requestID": "event_subscribe_anim_end",
                "messageType": "EventSubscriptionRequest",
                "data": {
                    "eventName": "ModelAnimationEvent",
                    "subscribe": True,
                    "config": {
                        "ignoreLive2DItems": True,
                        "ignoreIdleAnimations": True
                    }
                }
            })
            self.event_ws.send(request)
            response = self.event_ws.recv()
            response = json.loads(response)

            if 'subscribedEventCount' not in response['data']:
                raise Exception("VTS Hotkey Thread did not subscribe to event: {}".format(response))
            print("VTS Hotkey Thread subscribed to event")
        except Exception as err:
            print("VTS Hotkey Thread failed to subscribe to animation end event")
            print(err)
            raise err
        
        # Event loop
        while True:
            event = json.loads(self.event_ws.recv())
            if event["data"]["animationEventType"] == "End":
                self._trigger_hotkey_event.set()

    # Hotkeyer that runs in a separate thread
    # Continuously trigger configured VTube Studio hotkeys queued in self.hotkey_queue
    # Will keep self.hotkey_queue filled with idle animations so queue is never empty
    # Will iterate only once when awoken by _trigger_hotkey_event
    def _hotkey_exec_loop(self):
        while True:
            # Populate queue initially so there is something to play
            while len(self.hotkey_queue) < 10:
                self.hotkey_queue.append(random.choice(self.hotkey_map[self.DEFAULT_HOTKEY_SET]))

            # Request hotkey execution to VTS
            try:
                hotkey = self.hotkey_queue.pop(0)
                request = json.dumps({
                    "apiName": "VTubeStudioPublicAPI",
                    "apiVersion": "1.0",
                    "requestID": "message_hotkey",
                    "messageType": "HotkeyTriggerRequest",
                    "data": {
                        "hotkeyID": hotkey,
                    }
                })
                self.main_ws.send(request)
                response = self.main_ws.recv()
                response = json.loads(response)

                if 'hotkeyID' not in response['data']:
                    print(f"Hotkey on message failed: {response}")
            
                # Wait for next call to run hotkey if hotkey was not an animation
                # (non-animations are instant hotkeys that don't need to wait to finish)
                if hotkey in self.animations:
                    self._trigger_hotkey_event.wait()
                    self._trigger_hotkey_event.clear()

            except Exception as err:
                print(f"Failed to play hotkey: {err}")

    # Interprets emotion of input message and queues the corresponding hotkey in front
    def play_hotkey_using_message(self, message: str):
        # Perform sentiment analysis on message to detect emotion
        sentences = [message]
        model_outputs = self.classifier(sentences)
        result = model_outputs[0][0]['label']

        # Get hotkeys corresponding to emotion
        set_name = self.DEFAULT_HOTKEY_SET
        for set_key in self.emotion_map:
            if result in self.emotion_map[set_key]:
                set_name = set_key
                break
        
        # Select random hotkey from options
        hotkey = random.choice(self.hotkey_map[set_name])
        
        # Add to hotkey queue
        self.hotkey_queue.insert(0,hotkey)
        self._trigger_hotkey_event.set()
