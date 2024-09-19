
class EmptyRequestException(Exception):
    pass

class BaseT2TAIWorker():
    def __init__(self, prompt, **kwargs):
        self.prompt = prompt
        self.msg_history = []

    def __call__(self, new_msg: str, author: str):
        prompt = self._build_request()
        if prompt is None or len(prompt) == 1:
            raise EmptyRequestException()
        
        try:
            response = self.get_response(prompt, new_msg, author)
            response = self._trim_response(response)
        except Exception as err:
            response = 'There is a problem with my AI...'
        
        self._update_history(new_msg, author)
        self._update_history(response, 'J.A.I.son')
        return response
        
    
    def get_response(self, request: str):
        raise NotImplementedError
    
    def _update_history(self, new_msg: str, author: str):
        self.msg_history.append({
            "author": author,
            "message": new_msg if new_msg is not None else ''
        })
        if len(self.msg_history) > 10:
            self.msg_history.pop(0)

    def _build_script(self):
        script = ""
        for msg_obj in self.msg_history:
            script += f"\n[{msg_obj['author']}]: {msg_obj['message']}"

        return script
    
    def _build_request(self):
        return self.prompt + self._build_script()
    
    def _trim_response(self, response: str):
        return response.removeprefix('[J.A.I.son]: ')