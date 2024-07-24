from zhipuai import ZhipuAI
from keys import ZHIPUAI_API_KEY  # 假设你在keys.py中存储了智谱AI的API密钥
from prompts import create_prompt, INITIAL_RESPONSE
import time

client = ZhipuAI(api_key=ZHIPUAI_API_KEY)  # 请填写您自己的APIKey


# 生成基于转录文本的响应
def generate_response_from_transcript(transcript):
    try:
        response = client.chat.completions.create(
            model="GLM-4-0520",  # 填写需要调用的模型名称
            messages=[
                {"role": "user", "content": create_prompt(transcript)},
            ],
            stream=True,
        )
        full_response = ""
        for chunk in response:
            full_response += chunk.choices[0].delta.content  # 提取并连接 content 属性

        return full_response
    except Exception as e:
        print(f"API error: {e}")
        return ''


class ZhipuAiResponder:
    def __init__(self):
        self.response = INITIAL_RESPONSE
        self.response_interval = 2

    # 响应转录者，获取新的转录文本并生成响应
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

    # 更新响应时间间隔
    def update_response_interval(self, interval):
        self.response_interval = interval
