'''
Wrapper class for entire TTS pipeline. Used to generate speech from
text with a custom voice.

Requires: RVC-Project to be running, and a model to have been trained
Requires: Directory of working_file must exist (file doesn't have to)
'''

from .conversion.voice_changer import VoiceChangerAI
from .generation import model_dict
from config import config

class TTSAI():
    def __init__(
        self,
        tts_gen_model: str = 'openai',
        tts_con_model: str = 'mi_test',
        tts_con_server: str ='http://localhost:7865',
        working_file: str = 'output/audio/tts_raw.wav',
        **kwargs
    ):
        self.gen_model = model_dict[tts_gen_model](
            tts_output_filepath=config['tts_output_filepath']
        )
        self.con_model = VoiceChangerAI(
            tts_input_filepath=config['tts_output_filepath'],
            tts_output_filepath=config['rvc_output_filepath'],
            rvc_url=config['rvc_url'],
            rvc_model=config['rvc_model']
        )

    '''
    Generates speech file using the desired voice to speak the text msg.

    Returns (str) the filepath to the generated speech
    '''
    def __call__(self, msg: str):
        self.gen_model(msg)
        return self.con_model()
