class BaseTTSGenWorker():
    def __init__(self, tts_output_filepath: str = None, **kwargs):
        self.output_filepath = tts_output_filepath

    '''
    Main function for interacting with TTS generator.
    Called like BaseTTSGenWorker(msg)

    Parameters:
    - msg: Message to be spoken
    Returns: (str) filepath to generated speech file
    '''
    def __call__(self, msg: str):
        self.tts(msg)
        return self.output_filepath

    '''
    To be implemented. Functionality for interfacing with TTS generator.

    Parameters:
    - msg: Message to be spoken
    '''
    def tts(self, msg: str):
        raise NotImplementedError