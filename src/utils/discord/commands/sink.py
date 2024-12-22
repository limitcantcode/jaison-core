import datetime
import wave
from discord.ext import voice_recv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from utils.time import get_current_time
from utils.logging import create_sys_logger
logger = create_sys_logger(id='discord')

'''
Custom audio sink for managing call audio and triggering callback during silence.
This sink will save all recorded audio to buffer in memory. This buffer can be read
directly from this class at any time. Audio buffer will not be truncated until freshen(idx)
is called, to which all data up to and including idx will be truncated.
Audio is tracked per user in the call in the dictionary buf.
'''
class BufferSink(voice_recv.AudioSink):
    # Requires a callback function <fun(buf: BufferSink)> that will be called during silence
    # Callback accepts one arguement, and that is this BufferSink instance
    def __init__(self, stale_callback):
        self.buf = {}
        self.sample_width = 2
        self.sample_rate = 48000
        self.bytes_ps = 96000

        self.scheduler = AsyncIOScheduler()
        self.scheduler.start()
        self.stale_timer = None
        self.stale_callback = stale_callback

    def wants_opus(self):
        return False

	# just append data to the byte array
    def write(self, user, data):
        self.stale_timer = self.scheduler.add_job(
            self.stale_callback,
            'date',
            run_date=datetime.datetime.now()+datetime.timedelta(seconds=1),
            args=[self],
            id='vc_buffer_timer',
            replace_existing=True
        )
        if user.display_name not in self.buf:
            self.buf[user.display_name] = [None,bytearray()]
        if self.buf[user.display_name][0] is None:
            self.buf[user.display_name][0] = get_current_time()
        self.buf[user.display_name][1] += data.pcm
        
    def cleanup(self):
        self.scheduler.remove_job('vc_buffer_timer')
        self.scheduler.shutdown(wait=False)

    def freshen(self, user, idx: int = None):
        self.buf[user][0] = None
        self.buf[user][1] = self.buf[user][1][(idx or len(self.buf[user])):]

    def get_user_time(self, user):
        return self.buf[user][0]

    def save_user_to_file(self, user: str, filepath: str, idx: int = None):
        '''
        Returns index of last saved in buffer
        '''

        if user not in self.buf:
            raise Exception("User {} is not tracked in this audio buffer...".format(user))

        # Consume and measure
        curr_buff = self.buf[user][1][:(idx or len(self.buf[user][1]))]
        idx_consumed = len(curr_buff)

        # Save to file
        f = wave.open(filepath, 'wb')
        f.setnchannels(self.sample_width)
        f.setsampwidth(int(self.bytes_ps / self.sample_rate))
        f.setframerate(self.sample_rate)
        f.writeframes(curr_buff)
        f.close()

        return idx_consumed