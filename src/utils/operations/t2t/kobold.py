import requests

from utils.config import Config
from utils.processes import ProcessManager, ProcessType

from .base import T2TOperation

class KoboldT2T(T2TOperation):
    KOBOLD_LINK_ID = "kobold_t2t"
    
    def __init__(self):
        super().__init__("kobold")
        self.uri = None
        
    async def start(self) -> None:
        '''General setup needed to start generated'''
        await super().start()
        await ProcessManager().link(self.KOBOLD_LINK_ID, ProcessType.KOBOLD)
        self.uri = "http://127.0.0.1:{}".format(ProcessManager().get_process(ProcessType.KOBOLD).port)
    
    async def close(self) -> None:
        '''Clean up resources before unloading'''
        await super().close()
        await ProcessManager().unlink(self.KOBOLD_LINK_ID, ProcessType.KOBOLD)
    
    async def _generate(self, system_prompt: str = None, user_prompt: str = None, **kwargs):
        response = requests.post(
            "{}/api/v1/generate".format(self.uri), 
            json={
                "max_context_length": Config().kobold_t2t_max_context_length,
                "max_length": Config().kobold_t2t_max_length,
                "prompt": "<SYSTEM START>{}<SYSTEM END><USER START>{}<USER END".format(system_prompt, user_prompt),
                "quiet": Config().kobold_t2t_quiet,
                "rep_pen": Config().kobold_t2t_rep_pen,
                "rep_pen_range": Config().kobold_t2t_rep_pen_range,
                "rep_pen_slope": Config().kobold_t2t_rep_pen_slope,
                "temperature": Config().kobold_t2t_temperature,
                "tfs": Config().kobold_t2t_tfs,
                "top_a": Config().kobold_t2t_top_a,
                "top_k": Config().kobold_t2t_top_k,
                "top_p": Config().kobold_t2t_top_p,
                "typical": Config().kobold_t2t_typical
            },
        )

        if response.status_code == 200:
            result = response.json()['results'][0]['text']
            yield {"content": result}
        else:
            raise Exception(f"Failed to get T2T result: {response.status_code} {response.reason}")