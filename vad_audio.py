import collections
import queue

import pyaudio
import webrtcvad


class Audio:
    """
    Streams raw audio from microphone.
    Data is received in a separate thread, and stored in a buffer, to be read from.
    """
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    BLOCKS_PER_SECOND = 50

    FRAME_DURATION_MS = property(lambda self: 1000 * self.block_size // self.sample_rate)

    def __init__(self, sample_rate):
        self.sample_rate = sample_rate
        self.buffer_queue = queue.Queue()
        self.block_size = int(self.sample_rate / float(self.BLOCKS_PER_SECOND))

        self.chunk = None
        self.callback = lambda in_data: self.buffer_queue.put(in_data)

        def proxy_callback(in_data, frame_count, time_info, status):
            if self.chunk is not None:
                in_data = self.wf.readframes(self.chunk)
            self.callback(in_data)
            return None, pyaudio.paContinue

        kwargs = {
            'format': self.FORMAT,
            'channels': self.CHANNELS,
            'rate': self.sample_rate,
            'input': True,
            'frames_per_buffer': self.block_size,
            'stream_callback': proxy_callback,
        }
        self.pa = pyaudio.PyAudio()
        self.stream = self.pa.open(**kwargs)
        self.stream.start_stream()

    def __del__(self):
        self.stream.stop_stream()
        self.stream.close()
        self.pa.terminate()

    def read(self):
        """
        Return a block of audio data, blocking if necessary.
        """
        return self.buffer_queue.get()


class VadAudio(Audio):
    """
    Filter & segment audio with voice activity detection.
    """

    def __init__(self, aggressiveness, sample_rate):
        super().__init__(sample_rate=sample_rate)
        self.vad = webrtcvad.Vad(aggressiveness)

    def frame_generator(self):
        """
        Generator that yields all audio frames from microphone.
        """
        while True:
            yield self.read()

    def vad_collector(self, padding_ms=1000, ratio=0.75, frames=None):
        """
        Generator that yields series of consecutive audio frames comprising each utterence,
        separated by yielding a single None. Determines voice activity by ratio of frames in padding_ms.
        Uses a buffer to include padding_ms prior to being triggered.
        Example: (frame, ..., frame, None, frame, ..., frame, None, ...)
                 |---utterence---|        |---utterence---|
        """
        if frames is None:
            frames = self.frame_generator()

        num_padding_frames = padding_ms // self.FRAME_DURATION_MS
        ring_buffer = collections.deque(maxlen=num_padding_frames)
        triggered = False

        for frame in frames:
            if len(frame) < 640:
                return

            is_speech = self.vad.is_speech(frame, self.sample_rate)
            if not triggered:
                ring_buffer.append((frame, is_speech))
                num_voiced = len([f for f, speech in ring_buffer if speech])
                if num_voiced > ratio * ring_buffer.maxlen:
                    triggered = True
                    for f, s in ring_buffer:
                        yield f
                    ring_buffer.clear()

            else:
                yield frame
                ring_buffer.append((frame, is_speech))
                num_unvoiced = len([f for f, speech in ring_buffer if not speech])
                if num_unvoiced > ratio * ring_buffer.maxlen:
                    triggered = False
                    yield None
                    ring_buffer.clear()
