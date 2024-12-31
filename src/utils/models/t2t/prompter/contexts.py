import os
import json
from utils.observer import ObserverClient

class ContextBuilder():
    # This is the assumed format of the given contexts.
    # This will be added to the system prompt to explain
    #   how the user input will be formatted to provide
    #   context on the current situation
    DISABLED_CONTEXT_MESSAGE = "This context isn't provided."
    NO_RESPONSE = "<no response>"
    SELF_IDENTIFIER = "You"
    SCRIPT_HEADER = "=== SCRIPT ===="
    OTR_HEADER = "=== ONE TIME REQUEST ==="
    TWITCH_CHAT_HEADER = "=== TWITCH CHAT ===="
    TWITCH_EVENTS_HEADER = "=== TWITCH EVENTS ===="
    RAG_HEADER = "=== RAG ===="
    AV_HEADER = "=== AUDIO VISION ===="
    CONTEXT_INSTRUCTIONS = '''
The user is going to provide context on a currently ongoing conversation.

You are taking the next turn in a given conversation. This conversation will be given by the user along with other contexts. The conversation will be formatted as a script under the specific heading "{script_header}" where each line starts with time the line was spoken between [], then the speaker's name between [] or the special <{self_identifier}> to represent what you said before. For example:

{script_header}
[2024-12-09 20:51:46,339][Jason]: Hey there!
[2024-12-09 20:51:50,459]<{self_identifier}>: Oh hi!
[2024-12-09 20:51:52,354][Nosaj]: Hey

In the above example, "Jason" said "Hey there!". Then you said "Oh hi!". Finally "Nosaj" said "Hey".
You are to only respond with your own response to the current conversation, such as "Oh hi!". If you think you should not say anything, say "{no_response_token}". For example:

{script_header}
[2024-12-09 20:51:46,339][Jason]: Hey there!
[2024-12-09 20:51:50,459]<{self_identifier}>: Oh hi!
[2024-12-09 20:51:52,354][Jason]: I think I...

Here, you should return {no_response_token} so the conversation will now look like the following:

{script_header}
[2024-12-09 20:51:46,339][Jason]: Hey there!
[2024-12-09 20:51:50,459]<You>: Oh hi!
[2024-12-09 20:51:52,354][Jason]: I think I...
[2024-12-09 20:51:53,354]<You>: {no_response_token}

You will also recieve additional, optional context to the current situation. There will be special, one-time instructions that must be followed under the header "{otr_header}". There will also be a livestream chat from the streaming platform Twitch under the header "{twitch_chat_header}", latest livestream events under the header "{twitch_events_header}", retrieved information from the internet or long-term memory under the header "{rag_header}", and summaries from audio and vision models under the header "{av_header}".

You shall never break from the character described in the remainder of this system prompt:
'''.format(
    script_header=SCRIPT_HEADER,
    otr_header=OTR_HEADER,
    twitch_chat_header=TWITCH_CHAT_HEADER,
    twitch_events_header=TWITCH_EVENTS_HEADER,
    rag_header=RAG_HEADER,
    av_header=AV_HEADER,
    no_response_token=NO_RESPONSE,
    self_identifier=SELF_IDENTIFIER
)

    def __init__(self, jaison):
        self.jaison = jaison
        self.convo_history = [] # will contain {time: str, name: str, message: str}
        self.uncommited_history_len = 0

        self.event_listener = self.EventListener(self, jaison.twitch.broadcast_server)

        self.one_time_request = None
        self.twitch_latest_notif = None
        self.name_translations = {}

    class EventListener(ObserverClient):
        def __init__(self, parent, server):
            super().__init__(server=server)
            self.parent = parent

        def handle_event(self, event_id, payload) -> None:
            if event_id == 'twitch_event':
                self.parent.twitch_latest_notif = payload['event']

    def get_context_instructions(self):
        return self.CONTEXT_INSTRUCTIONS

    def translate_name(self, name):
        try:
            return self.name_translations[name]
        except:
            return name

    def add_history(self, time, name, message):
        self.convo_history.append({
            "time": time,
            "name": name,
            "message": message
        })
        self.uncommited_history_len += 1

    def rollback_history(self):
        if self.uncommited_history_len > 0:
           self.convo_history = self.convo_history[:-(self.uncommited_history_len)]

        self.uncommited_history_len = 0

    def commit_history(self):
        self.convo_history = self.convo_history[-(self.jaison.config.t2t_convo_retention_length or 20):]
        self.uncommited_history_len = 0

    def get_uncommited_history(self):
        return self.convo_history[-(self.uncommited_history_len):] if self.uncommited_history_len > 0 else []

    def reload_name_translations(self):
        with open(os.path.join(self.jaison.config.t2t_name_translation_dir, self.jaison.config.t2t_name_translation_file), 'r') as f:
            self.name_translations = json.load(f)

    def msg_o_to_line(self, o):
        time = "[{}]".format(o['time'])
        name = "<{}>".format(self.SELF_IDENTIFIER) if o['name'] == self.SELF_IDENTIFIER else "[{}]".format(self.translate_name(o['name']))
        message = o['message']

        return f"{time} {name}: {message}\n"

    def get_context_script(self):
        script = ""
        self.reload_name_translations()
        for o in self.convo_history:
            script += self.msg_o_to_line(o)
        
        return script

    def get_one_time_request(self):
        context = self.one_time_request or "There is no request."
        self.one_time_request = None
        return context


    def get_context_twitch_chat(self):
        if self.jaison.config.t2t_enable_context_twitch_chat:
            chat_history = self.jaison.twitch_get_chat_history()
            if len(chat_history) == 0:
                return "Chat is empty right now."

            result = ""
            for chat in chat_history:
                result += "[{}]: {}\n".format(chat['name'], chat['message'])
            return result

        return self.DISABLED_CONTEXT_MESSAGE

    def get_context_twitch_events(self):
        if self.jaison.config.t2t_enable_context_twitch_events:
            if self.twitch_latest_notif is None:
                return "Nothing has happened."
            result = self.twitch_latest_notif
            self.twitch_latest_notif = None
            return result

        return self.DISABLED_CONTEXT_MESSAGE

    def get_context_rag(self):
        if self.jaison.config.t2t_enable_context_rag:
            return self.DISABLED_CONTEXT_MESSAGE # TODO

        return self.DISABLED_CONTEXT_MESSAGE

    def get_context_av(self):
        if self.jaison.config.t2t_enable_context_av:
            return self.DISABLED_CONTEXT_MESSAGE # TODO

        return self.DISABLED_CONTEXT_MESSAGE

    def get_context_final(self):
        return '''
{otr_header}
{otr}

{twitch_chat_header}
{twitch_chat}

{twitch_events_header}
{twitch_events}

{rag_header}
{rag}

{av_header}
{av}

{script_header}
{script}
'''.format(
    otr_header=self.OTR_HEADER,
    otr=self.get_one_time_request(),
    script_header=self.SCRIPT_HEADER,
    script=self.get_context_script(),
    twitch_chat_header=self.TWITCH_CHAT_HEADER,
    twitch_chat=self.get_context_twitch_chat(),
    twitch_events_header=self.TWITCH_EVENTS_HEADER,
    twitch_events=self.get_context_twitch_events(),
    rag_header=self.RAG_HEADER,
    rag=self.get_context_rag(),
    av_header=self.AV_HEADER,
    av=self.get_context_av()
)

    def set_one_time_request_context(self, message):
        self.one_time_request = message
        return True