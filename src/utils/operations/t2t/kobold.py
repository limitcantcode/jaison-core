import requests

from utils.processes import ProcessManager, ProcessType

from .base import T2TOperation
from utils.prompter.message import ChatMessage
from utils.prompter import Prompter

class KoboldT2T(T2TOperation):
    KOBOLD_LINK_ID = "kobold_t2t"
    
    def __init__(self):
        super().__init__("kobold")
        self.uri = None
        
        self.max_context_length: int = 2048
        self.max_length: int = 100
        self.rep_pen: float = 1.1
        self.rep_pen_range: int = 256
        self.rep_pen_slope: int = 1
        self.temperature: float = 0.5
        self.tfs: int = 1
        self.top_a: int = 0
        self.top_k: int = 100
        self.top_p: float = 0.9
        self.typical: int = 1
        
    async def start(self) -> None:
        '''General setup needed to start generated'''
        await super().start()
        await ProcessManager().link(self.KOBOLD_LINK_ID, ProcessType.KOBOLD)
        self.uri = "http://127.0.0.1:{}".format(ProcessManager().get_process(ProcessType.KOBOLD).port)
    
    async def close(self) -> None:
        '''Clean up resources before unloading'''
        await super().close()
        await ProcessManager().unlink(self.KOBOLD_LINK_ID, ProcessType.KOBOLD)
    
    async def configure(self, config_d):
        '''Configure and validate operation-specific configuration'''
        if "max_context_length" in config_d: self.max_context_length = config_d["max_context_length"]
        if "max_length" in config_d: self.max_length = config_d["max_length"]
        if "rep_pen" in config_d: self.rep_pen = config_d["rep_pen"]
        if "rep_pen_range" in config_d: self.rep_pen_range = config_d["rep_pen_range"]
        if "rep_pen_slope" in config_d: self.rep_pen_slope = config_d["rep_pen_slope"]
        if "temperature " in config_d: self.temperature  = config_d["temperature "]
        if "tfs" in config_d: self.tfs = config_d["tfs"]
        if "top_a" in config_d: self.top_a = config_d["top_a"]
        if "top_k" in config_d: self.top_k = config_d["top_k"]
        if "top_p" in config_d: self.top_p = config_d["top_p"]
        if "typical" in config_d: self.typical = config_d["typical"]
        
        assert self.max_context_length > 0
        assert self.max_length > 0
        assert self.rep_pen > 0 # TODO check the limits
        assert self.rep_pen_range > 0
        assert self.rep_pen_slope > 0
        assert self.temperature > 0
        assert self.tfs > 0
        assert self.top_a > 0
        assert self.top_k > 0
        assert self.top_p > 0
        assert self.typical > 0
        
    async def get_configuration(self):
        '''Returns values of configurable fields'''
        return {
            "max_context_length": self.max_context_length,
            "max_length": self.max_length,
            "rep_pen": self.rep_pen,
            "rep_pen_range": self.rep_pen_range,
            "rep_pen_range": self.rep_pen_range,
            "rep_pen_slope": self.rep_pen_slope,
            "temperature": self.temperature,
            "tfs": self.tfs,
            "top_a": self.top_a,
            "top_k": self.top_k,
            "top_p": self.top_p,
            "typical": self.typical,
        }

    async def _generate(self, instruction_prompt: str = None, messages: list = None, **kwargs):
        history = [{ "role": "system", "content": instruction_prompt }]
        for msg in messages:
            next_hist = None
            if isinstance(msg, ChatMessage) and msg.user == Prompter().character_name:
                next_hist = { "role": "assistant", "content": msg.message }
            else:
                next_hist = { "role": "user", "content": msg.to_line() }
            history.append(next_hist)

        response = requests.post(
            "{}/v1/chat/completions".format(self.uri), 
            json={
                "model": "kcpp",
                "messages": history,
                "max_context_length": self.max_context_length,
                "max_length": self.max_length,
                "quiet": True,
                "rep_pen": self.rep_pen,
                "rep_pen_range": self.rep_pen_range,
                "rep_pen_slope": self.rep_pen_slope,
                "temperature": self.temperature,
                "tfs": self.tfs,
                "top_a": self.top_a,
                "top_k": self.top_k,
                "top_p": self.top_p,
                "typical": self.typical
            },
        )

        if response.status_code == 200:
            result = response.json()['choices'][0]['message']['content']
            yield {"content": result}
        else:
            raise Exception(f"Failed to get T2T result: {response.status_code} {response.reason}")