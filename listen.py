import os
import sys
import deepspeech
import numpy as np
from halo import Halo

from vad_audio import VadAudio

# ----------------------------------------------------------------------------------------------------------------------
DEFAULT_SAMPLE_RATE = 16000
VAD_AGGRESSIVENESS = 1  # 0 -> 3, 0 means the least aggressive, 3 the most aggressive

MODELS_PATH = 'models'
# ----------------------------------------------------------------------------------------------------------------------

def get_model():
    files = os.listdir(MODELS_PATH)
    models = [model for model in files if '.pbmm' in model]
    if len(models) > 1:
        print(f"More than one .pbmm file in {MODELS_PATH} folder!")
        sys.exit(-1)

    return models[0]


def main():
    print('Initializing model...')
    model_name = get_model()
    model_path = os.path.join(MODELS_PATH, model_name)
    model = deepspeech.Model(model_path)

    # start audio with VAD
    print("Listening (ctrl-C to exit)...")
    vad_audio = VadAudio(aggressiveness=VAD_AGGRESSIVENESS,
                         sample_rate=DEFAULT_SAMPLE_RATE)
    frames = vad_audio.vad_collector()
    spinner = Halo(spinner='line')

    # stream from microphone to DeepSpeech using VAD
    stream_context = model.createStream()
    for frame in frames:
        if frame is not None:
            if spinner:
                spinner.start()
            stream_context.feedAudioContent(np.frombuffer(frame, np.int16))
        else:
            if spinner:
                spinner.stop()
            text = stream_context.finishStream()
            print("Recognized: " + text)
            stream_context = model.createStream()


if __name__ == '__main__':
    main()
