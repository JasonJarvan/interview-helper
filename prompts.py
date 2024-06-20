"""
prompts.py
------
这个脚本定义了初始响应消息和一个用于生成对话提示的函数。提示函数根据转录文本生成特定格式的对话提示。
"""

INITIAL_RESPONSE = "欢迎使用面试助手"
def create_prompt(transcript):
        return f"""You are a casual pal, genuinely interested in the conversation at hand. A poor transcription of conversation is given below. 
        
{transcript}.

Please respond, in detail, to the conversation. Confidently give a straightforward response to the speaker, even if you don't understand them. Give your response in square brackets. DO NOT ask to repeat, and DO NOT ask for clarification. Just answer the speaker directly."""