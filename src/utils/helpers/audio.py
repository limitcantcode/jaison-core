import wave
import ffmpeg

from utils.config import Config

def pitch_audio(ab: bytes, sr: int, sw: int, ch: int, pitch_amount: int):
    # ffmpeg -i "input.wav" -af "rubberband=smoothing=on:pitch=2^(1/2):pitchq=quality:window=short:channels=apart:phase=independent" "output.wav"
    speed_factor = 2 ** (pitch_amount/12)
    
    with wave.open(Config().ffmpeg_working_src, 'wb') as f:
        f.setframerate(sr)
        f.setsampwidth(sw)
        f.setnchannels(ch)
        f.writeframes(ab)
        
    ffmpeg.input(
        Config().ffmpeg_working_src
    ).filter(
        "atempo",
        1/speed_factor
    ).filter(
        "asetrate",
        sr*speed_factor
    ).output(
        Config().ffmpeg_working_dest
    ).run(
        overwrite_output=True,
        quiet=True
    )
    with wave.open(Config().ffmpeg_working_dest, 'r') as f:
        return f.readframes(f.getnframes()), f.getframerate(), f.getsampwidth(), f.getnchannels()
