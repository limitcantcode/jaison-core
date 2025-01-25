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
import shutil
from utils.logging import create_sys_logger
logger = create_sys_logger()

class VoiceChangerAI():
    def __init__(self, config):
        self.config = config
        self.current_model = None

    # Force update with new config changes
    def reload(self):
        client = Client(self.config.ttsc_url)
        if self.current_model != self.config.ttsc_voice:
            logger.debug("Different voice detected. Updating...")
            self.current_model = self.config.ttsc_voice
            client.predict(
                f"{self.config.ttsc_voice}.pth",
                0,
                0,
                api_name='/infer_change_voice'
            )
            logger.debug("Updated")
        return client

    '''
    Converts voice in input file to the voice trained using the RVC model
    to a new voice, storing conversion in output file (files as configured
    at runtime)

    Returns (str) the filepath to the converted speech file
    '''
    def __call__(self):
        logger.debug(f"Got request to convert {self.config.RESULT_TTSG}")
        client = self.reload()

        # Convert on local RVC-Project server
        logger.debug("")
        result = client.predict(
            0, # speaker id
            self.config.RESULT_TTSG, # target wav file
            self.config.ttsc_transpose,
            os.path.join(os.path.dirname(os.path.realpath(__file__)),'empty.txt'), # optional f0 curve
            'rmvpe', # pitch algo
            '', # index filepath
            '', # index auto
            self.config.ttsc_feature_ratio,
            self.config.ttsc_median_filtering,
            self.config.ttsc_resampling,
            self.config.ttsc_volume_envelope,
            self.config.ttsc_voiceless_protection,
            api_name='/infer_convert'
        )

        logger.debug("Service finished conversion. Copying result...")   
        # Copy output data from RVC to destination
        shutil.copy(result[1], self.config.RESULT_TTSC)

        logger.debug("Result finished.") 
        return True