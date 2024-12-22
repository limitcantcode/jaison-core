class BaseTTSGenModel():
    def __init__(self, config):
        self.config = config

    '''
    Main function for interacting with TTS generator.
    Called like BaseTTSGenModel(msg)

    Parameters:
    - content: Message to be spoken
    - out_filepath: Filepath to store result
    '''
    def __call__(self, content: str):
        raise NotImplementedError