import threading
from AudioTranscriber import AudioTranscriber
from ZhipuAiResponder import ZhipuAiResponder
from GPTResponder import GPTResponder
import customtkinter as ctk
import AudioRecorder
import queue
import time
import torch
import sys
import TranscriberModels
import subprocess
from tkinter import PhotoImage


# 这个方法清空给定的文本框，并将新文本插入其中。
def write_in_textbox(textbox, text):
    textbox.delete("0.0", "end")
    textbox.insert("0.0", text)


# 该方法从transcriber获取转录文本，并更新到UI的文本框中。使用after方法设置每300毫秒更新一次。
def update_transcript_UI(transcriber, textbox):
    transcript_string = transcriber.get_transcript()
    write_in_textbox(textbox, transcript_string)
    textbox.after(300, update_transcript_UI, transcriber, textbox)


# 这个方法更新响应文本框，控制响应更新的间隔，并根据滑块设置更新间隔时间。使用after方法设置每300毫秒更新一次。
def update_response_UI(responder, textbox, update_interval_slider_label, update_interval_slider, freeze_state):
    if not freeze_state[0]:
        response = responder.response

        textbox.configure(state="normal")
        write_in_textbox(textbox, response)
        textbox.configure(state="disabled")

        update_interval = int(update_interval_slider.get())
        responder.update_response_interval(update_interval)
        update_interval_slider_label.configure(text=f"询问间隔: {update_interval} 秒")

    textbox.after(300, update_response_UI, responder, textbox, update_interval_slider_label, update_interval_slider,
                  freeze_state)


# 该方法清除转录数据和音频队列中的内容。
def clear_context(transcriber, audio_queue):
    transcriber.clear_transcript_data()
    with audio_queue.mutex:
        audio_queue.queue.clear()


# 该方法创建和配置UI组件，包括文本框、按钮和滑块。
def create_ui_components(root):
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")
    root.title("面试助手")
    root.configure(bg='#FFFFFF')
    root.geometry("1000x600")

    icon_image = PhotoImage(file="./pictures/RCLogo.png")
    root.iconphoto(False, icon_image)

    font_size = 20

    transcript_textbox = ctk.CTkTextbox(root, width=300, font=("Arial", font_size), text_color='#000000', wrap="word",
                                        fg_color='#FFFFFF')
    transcript_textbox.grid(row=0, column=0, padx=10, pady=20, sticky="nsew")

    response_textbox = ctk.CTkTextbox(root, width=300, font=("Arial", font_size), text_color='#000000', wrap="word",
                                      fg_color='#FFFFFF')
    response_textbox.grid(row=0, column=1, padx=10, pady=20, sticky="nsew")

    freeze_button = ctk.CTkButton(root, text="Freeze", fg_color='#E0E0E0', text_color='#000000')
    freeze_button.grid(row=1, column=1, padx=10, pady=3, sticky="nsew")

    update_interval_slider_label = ctk.CTkLabel(root, text=f"", font=("Arial", 12), text_color="#000000")
    update_interval_slider_label.grid(row=2, column=1, padx=10, pady=3, sticky="nsew")

    update_interval_slider = ctk.CTkSlider(root, from_=1, to=10, width=300, height=20, number_of_steps=9)
    update_interval_slider.set(2)
    update_interval_slider.grid(row=3, column=1, padx=10, pady=10, sticky="nsew")

    return transcript_textbox, response_textbox, update_interval_slider, update_interval_slider_label, freeze_button


def main():
    # FFmpeg检查
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        print("ERROR: The ffmpeg library is not installed. Please install ffmpeg and try again.")
        return

    # 创建UI主窗口和组件。
    root = ctk.CTk()
    transcript_textbox, response_textbox, update_interval_slider, update_interval_slider_label, freeze_button = create_ui_components(
        root)

    # 设置用户和扬声器的音频录制，并将音频数据录制到队列中。
    audio_queue = queue.Queue()

    user_audio_recorder = AudioRecorder.DefaultMicRecorder()
    user_audio_recorder.record_into_queue(audio_queue)

    time.sleep(2)

    speaker_audio_recorder = AudioRecorder.DefaultSpeakerRecorder()
    speaker_audio_recorder.record_into_queue(audio_queue)

    # 初始化转录模型和响应生成器，并启动相应的线程。
    model = TranscriberModels.get_model('--api' in sys.argv)

    transcriber = AudioTranscriber(user_audio_recorder.source, speaker_audio_recorder.source, model)
    transcribe = threading.Thread(target=transcriber.transcribe_audio_queue, args=(audio_queue,))
    transcribe.daemon = True
    transcribe.start()

    # todo 目前项目集合了GPT和智谱AI两个模型，分别初始化并启动相应的线程（启用1个模型就行）。

    # 初始化GPT响应生成器，并启动相应的线程。
    # responder = GPTResponder()

    # 初始化智谱响应生成器，并启动相应的线程。
    responder = ZhipuAiResponder()

    respond = threading.Thread(target=responder.respond_to_transcriber, args=(transcriber,))
    respond.daemon = True
    respond.start()

    # 配置UI的网格布局，添加清除转录按钮和冻结按钮的功能，设置UI更新事件并启动主循环。
    print("READY")

    root.grid_rowconfigure(0, weight=100)
    root.grid_rowconfigure(1, weight=1)
    root.grid_rowconfigure(2, weight=1)
    root.grid_rowconfigure(3, weight=1)
    root.grid_columnconfigure(0, weight=2)
    root.grid_columnconfigure(1, weight=1)

    # Add the clear transcript button to the UI
    clear_transcript_button = ctk.CTkButton(root, text="清空转录记录",
                                            command=lambda: clear_context(transcriber, audio_queue, ))
    clear_transcript_button.grid(row=1, column=0, padx=10, pady=3, sticky="nsew")

    freeze_state = [False]  # Using list to be able to change its content inside inner functions

    def freeze_unfreeze():
        freeze_state[0] = not freeze_state[0]  # Invert the freeze state
        freeze_button.configure(text="解冻" if freeze_state[0] else "冻结")

    freeze_button.configure(command=freeze_unfreeze)

    update_interval_slider_label.configure(text=f"询问间隔： {update_interval_slider.get()} 秒")

    update_transcript_UI(transcriber, transcript_textbox)
    update_response_UI(responder, response_textbox, update_interval_slider_label, update_interval_slider, freeze_state)

    root.mainloop()


if __name__ == "__main__":
    main()
