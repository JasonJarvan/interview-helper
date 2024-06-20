"""
TranscriberModels.py
------
这个脚本定义了获取音频转录模型的函数和两个实现转录功能的类（WhisperTranscriber 和 APIWhisperTranscriber）。根据是否使用API，返回相应的模型对象。
"""

import openai
import whisper
import os
import torch

# 根据是否使用API，返回相应的音频转录模型对象。
def get_model(use_api):
    if use_api:
        return APIWhisperTranscriber()
    else:
        return WhisperTranscriber()
# WhisperTranscriber 类使用 Whisper 模型进行音频转录。
class WhisperTranscriber:
    # 初始化 WhisperTranscriber 对象，加载 Whisper 模型。
    def __init__(self):
        self.audio_model = whisper.load_model(os.path.join(os.getcwd(), 'whisper_models','tiny.pt'))
        print(f"[INFO] Whisper using GPU: " + str(torch.cuda.is_available()))

    # 获取音频文件的转录文本。
    def get_transcription(self, wav_file_path):
        try:
            result = self.audio_model.transcribe(wav_file_path, fp16=torch.cuda.is_available())
        except Exception as e:
            print(e)
            return ''
        return result['text'].strip()

# APIWhisperTranscriber 类使用 OpenAI 的 Whisper API 进行音频转录。
class APIWhisperTranscriber:
    # 获取音频文件的转录文本。
    def get_transcription(self, wav_file_path):
        try:
            with open(wav_file_path, "rb") as audio_file:
                result = openai.Audio.transcribe("whisper-1", audio_file)
        except Exception as e:
            print(e)
            return ''
        return result['text'].strip()
