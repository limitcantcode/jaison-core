from .models.stt import STTWorker
from .models.t2t import T2TWorker
from .models.ttsg import TTSGWorker
from .models.ttsc import TTSCWorker

COMPONENT_COLLECTION = {
    "stt": STTWorker,
    "t2t": T2TWorker,
    "ttsg": TTSGWorker,
    "ttsc": TTSCWorker
}