
NUMBERS = {
    'zero': 0,
    'one': 1,
    'two': 2,
    'three': 3,
    'four': 4,
}

DIRECTIONS = {
    'backward': 0,
    'forward': 1,
}


class VoiceMessage:
    def __init__(self):
        self.command = 0
        self.train = None
        self.speed = None
        self.direction = 1
        self.valid = False
    
    def __call__(self):
        if not self.valid:
            raise RuntimeError('Unrecognized message!')

        if self.command == 0:
            return str(self.command)
        elif self.command == 1:
            if self.train is None:
                raise RuntimeError('Unrecognized train!')
            return ' '.join([str(self.command), str(self.train)])
        else:
            if self.train is None:
                raise RuntimeError('Unrecognized train!')
            if self.speed is None:
                raise RuntimeError('Unrecognized speed!')
            if self.direction is None:
                raise RuntimeError('Unrecognized direction!')
            return ' '.join([
                str(self.command), str(self.train),
                str(self.speed), str(self.direction)
            ])


class CommandTranslator:
    def __init__(self) -> None:
        pass

    def recognize_command(self, message: str) -> str:
        voice_message = VoiceMessage()
        if 'pkm' in message:
            voice_message.valid = True
        if 'stop all' in message:
            voice_message.command = 0
        elif 'stop' in message:
            voice_message.command = 1
        elif 'start' in message:
            voice_message.command = 2
        else:
            raise RuntimeError('Unrecognized command!')

        message_list = message.split(' ')
        for i, word in enumerate(message_list):
            if word == 'train':
                voice_message.train = NUMBERS.get(message_list[i+1])
            
            if word == 'speed':
                voice_message.speed = NUMBERS.get(message_list[i+1])

            if word == 'direction':
                voice_message.direction = DIRECTIONS.get(message_list[i+1])

        return voice_message()
