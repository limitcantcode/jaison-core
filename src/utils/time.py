import datetime
from dateutil import tz

def get_current_time(include_ms: bool = True, as_str: bool = True):
    time = datetime.datetime.now()

    if include_ms:
        time = time.replace(microsecond=0)
    time = time.astimezone(tz.tzlocal())
    if as_str:
        time = time.isoformat()
        
    return time