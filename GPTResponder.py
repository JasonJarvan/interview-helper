"""
GPTResponder.py
------
这个脚本定义了一个类 GPTResponder，用于基于转录文本生成响应。它通过 OpenAI 的 GPT 模型生成响应，并控制响应生成的时间间隔。
"""

import openai
from keys import OPENAI_API_KEY
from prompts import create_prompt, INITIAL_RESPONSE
import time

openai.api_key = OPENAI_API_KEY


# 生成基于转录文本的响应。
def generate_response_from_transcript(transcript):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0301",
            messages=[{"role": "system", "content": create_prompt(transcript)}],
            temperature=0.0
        )
    except Exception as e:
        print(e)
        return ''
    full_response = response.choices[0].message.content
    try:
        return full_response.split('[')[1].split(']')[0]
    except:
        return ''


# GPTResponder 类用于管理 GPT 响应生成和更新响应时间间隔。
class GPTResponder:
    def __init__(self):
        self.response = INITIAL_RESPONSE
        self.response_interval = 2

    # 响应转录者，获取新的转录文本并生成响应。
    def respond_to_transcriber(self, transcriber):
        while True:
            if transcriber.transcript_changed_event.is_set():
                start_time = time.time()

                transcriber.transcript_changed_event.clear()
                transcript_string = transcriber.get_transcript()
                response = generate_response_from_transcript(transcript_string)

                end_time = time.time()  # Measure end time
                execution_time = end_time - start_time  # Calculate the time it took to execute the function

                if response != '':
                    self.response = response

                remaining_time = self.response_interval - execution_time
                if remaining_time > 0:
                    time.sleep(remaining_time)
            else:
                time.sleep(0.3)

    # 更新响应时间间隔。
    def update_response_interval(self, interval):
        self.response_interval = interval
