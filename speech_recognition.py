import os
import sys
import threading
import deepspeech
import numpy as np
from halo import Halo

from command_translator import CommandTranslator
from tcp_client import TcpClient
from vad_audio import VadAudio


class SpeechRecognition:
    __MODELS_PATH = 'models'
    __DEFAULT_SAMPLE_RATE = 16000
    __VAD_AGGRESSIVENESS = 0

    def __init__(self) -> None:
        self.__model = deepspeech.Model(self.__get_model_path())
        self.__tcp_client = TcpClient()
        self.__command_translator = CommandTranslator()
        self.__listening_active = False

        self.__listen_thread = threading.Thread(name="Listen Thread",
                                                target=self.__run_listening_thread)
        self.__send_thread = threading.Thread(name="Send Thread",
                                              target=self.__run_sending_thread)


    def run(self):
        self.__listen_thread.start()

        while True:
            self.__send_thread.start()
            self.__send_thread.join()
            self.__print('Send thread is done')
            self.__send_thread = threading.Thread(name="Send Thread",
                                                  target=self.__run_sending_thread)

    def stop(self):
        self.__tcp_client.stop()

    def __get_model_path(self):
        files = os.listdir(self.__MODELS_PATH)
        models = [model for model in files if '.pbmm' in model]
        if len(models) > 1:
            print(f"SpeechRecognition: More than one .pbmm file in {self.__MODELS_PATH} folder!")
            sys.exit(-1)

        return os.path.join(self.__MODELS_PATH, models[0])

    def __run_sending_thread(self):
        self.__tcp_client.connect()
        self.__listening_active = True
        self.__tcp_client.run()
        self.__listening_active = False

    def __run_listening_thread(self):
        while not self.__listening_active:
            continue

        self.__print('Start Recognition')

        vad_audio = VadAudio(aggressiveness=self.__VAD_AGGRESSIVENESS,
                             sample_rate=self.__DEFAULT_SAMPLE_RATE)
        frames = vad_audio.vad_collector()
        stream_context = self.__model.createStream()
        for frame in frames:
            if self.__listening_active:
                if frame is not None:
                    stream_context.feedAudioContent(np.frombuffer(frame, np.int16))
                else:
                    text = stream_context.finishStream()
                    self.__print('Recognized: ' + text)
                    self.__translate(text)
                    stream_context = self.__model.createStream()

    def __translate(self, message):
        try:
            command = self.__command_translator.recognize_command(message)
            self.__print('Translated into: ' + command)
            self.__tcp_client.put_message(bytes(command, encoding='utf8'))

        except RuntimeError as e:
            self.__print('Error: ' + str(e))

    @staticmethod
    def __print(message):
        print(f"SpeechRecognition: {message}")