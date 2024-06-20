"""
AudioRecorder.py
------
这个脚本定义了音频录制相关的类，用于从默认麦克风和扬声器捕获音频数据，并将音频数据放入队列中进行处理。包括基类 BaseRecorder 和两个子类 DefaultMicRecorder 和 DefaultSpeakerRecorder。
"""

import custom_speech_recognition as sr
import pyaudiowpatch as pyaudio
from datetime import datetime

RECORD_TIMEOUT = 3
ENERGY_THRESHOLD = 1000
DYNAMIC_ENERGY_THRESHOLD = False

#BaseRecorder 是一个基类，用于记录音频
class BaseRecorder:
    
    #初始化 BaseRecorder 对象。它接受一个音频源（source）和一个源名称（source_name）作为参数。它创建了一个 Recognizer 对象，并设置了能量阈值和动态能量阈值。如果音频源为 None，则会引发 ValueError。
    
    def __init__(self, source, source_name):
        self.recorder = sr.Recognizer()
        self.recorder.energy_threshold = ENERGY_THRESHOLD
        self.recorder.dynamic_energy_threshold = DYNAMIC_ENERGY_THRESHOLD

        if source is None:
            raise ValueError("audio source can't be None")

        self.source = source
        self.source_name = source_name
    #此方法用于调整环境噪音。它打印一条信息消息，然后使用 self.source 对象调整环境噪音。
    def adjust_for_noise(self, device_name, msg):
        print(f"[INFO] Adjusting for ambient noise from {device_name}. " + msg)
        with self.source:
            self.recorder.adjust_for_ambient_noise(self.source)
        print(f"[INFO] Completed ambient noise adjustment for {device_name}.")
    #此方法用于在后台监听音频，并将音频数据放入队列。它定义了一个内部回调函数 record_callback，该函数在检测到音频时将音频数据放入队列。然后，它使用 self.source 对象和回调函数来开始监听音频。
    def record_into_queue(self, audio_queue):
        def record_callback(_, audio:sr.AudioData) -> None:
            data = audio.get_raw_data()
            audio_queue.put((self.source_name, data, datetime.utcnow()))

        self.recorder.listen_in_background(self.source, record_callback, phrase_time_limit=RECORD_TIMEOUT)
#DefaultMicRecorder 是一个继承自 BaseRecorder 的类。它的初始化方法 __init__ 中，它调用了父类 BaseRecorder 的初始化方法，并传入了一个 sr.Microphone 对象作为音频源，以及源名称 "You"。
#然后，它调用了 adjust_for_noise 方法，用于调整环境噪音，传入的参数分别是设备名称 "Default Mic" 和提示信息 "Please make some noise from the Default Mic..."。
class DefaultMicRecorder(BaseRecorder):
    #初始化 DefaultMicRecorder 对象，并设置音频源和源名称。
    def __init__(self):
        super().__init__(source=sr.Microphone(sample_rate=16000), source_name="You")
        self.adjust_for_noise("Default Mic", "Please make some noise from the Default Mic...")

# DefaultSpeakerRecorder 是一个继承自 BaseRecorder 的类。它的初始化方法 __init__ 中，首先获取默认扬声器设备的信息，如果找不到回放设备则抛出错误。之后，调用父类的初始化方法并调整环境噪音。
class DefaultSpeakerRecorder(BaseRecorder):
    def __init__(self):
        with pyaudio.PyAudio() as p:
            wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
            default_speakers = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])
            
            if not default_speakers["isLoopbackDevice"]:
                for loopback in p.get_loopback_device_info_generator():
                    if default_speakers["name"] in loopback["name"]:
                        default_speakers = loopback
                        break
                else:
                    print("[ERROR] No loopback device found.")
        
        source = sr.Microphone(speaker=True,
                               device_index= default_speakers["index"],
                               sample_rate=int(default_speakers["defaultSampleRate"]),
                               chunk_size=pyaudio.get_sample_size(pyaudio.paInt16),
                               channels=default_speakers["maxInputChannels"])
        super().__init__(source=source, source_name="Speaker")
        self.adjust_for_noise("Default Speaker", "Please make or play some noise from the Default Speaker...")