'''
This class makes use of the RVC-Project (https://github.com/limitcantcode/Retrieval-based-Voice-Conversion-WebUI)
to convert generated speech files from any voice to your desired voice.
Please download and follow the instructions in the README (there's an 
english translation in the docs/ directory) to train a model with the 
desired voice.

NOTE: The RVC gradio web-UI must be running before this project. 
This is done by running the ./infer-web.py in that repo.
'''

from gradio_client import Client
import os

class VoiceChangerAI():
    def __init__(
        self,
        tts_input_filepath=None,
        tts_output_filepath=None, # filepath to convert (.wav)
        rvc_url=None, # RVC-Project webserve available here: https://github.com/limitcantcode/Retrieval-based-Voice-Conversion-WebUI
        rvc_model=None, # name of model from RVC. E.g. 'mi-test'
        **kwargs
    ):
        self.input_filepath = tts_input_filepath
        self.output_filepath = tts_output_filepath
        self.client = Client(rvc_url)
        self.client.predict(
            rvc_model+'.pth',
            0,
            0,
            api_name='/infer_change_voice'
        )
        print(f"Connected to RVC server: {rvc_url}")

    '''
    Converts voice in input file to the voice trained using the RVC model
    to a new voice, storing conversion in output file (files as configured
    at runtime)

    Returns (str) the filepath to the converted speech file
    '''
    def __call__(self):
        # Convert on local RVC-Project webserver
        result = self.client.predict(
            0, # speaker id
            self.input_filepath, # target wav file
            0, # transpose
            os.path.join(os.path.dirname(os.path.realpath(__file__)),'empty.txt'), # optional f0 curve
            'rmvpe', # pitch algo
            '', # index filepath
            '', # index auto
            0, # feature ratio
            7, # median filtering
            0, # resampling
            0, # volume envelope
            0.5, # voiceless consonant protection
            api_name='/infer_convert'
        )
        
        # Copy output data to destination
        audio_file = open(result[1], 'rb')
        output = open(self.output_filepath, 'wb')
        output.write(audio_file.read())
        audio_file.close()
        output.close()

        return self.output_filepath