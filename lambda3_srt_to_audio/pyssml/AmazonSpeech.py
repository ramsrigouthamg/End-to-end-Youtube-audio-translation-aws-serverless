""" AmazonSpeech is an add on for PySSML to support tags unique to Amazon

1. Create a AmazonSpeech(PySSML) object
    s = AmazonSpeech()

2. Add your speech text
    s.say('Hello')
    s.whisper('Brad')

3. Retrieve your SSML
    s.ssml()      # to retrieve ssml with <speak> wrapper
    s.ssml(True)  # to retrieve ssml without <speak> wrapper
    s.to_object() # to retrieve complete speach output object

"""
from pyssml.PySSML import PySSML


class AmazonSpeech(PySSML):

    def __init__(self):
        super().__init__()

    def whisper(self, words):
        if words is None:
            raise TypeError('Parameter words must not be None')
        try:
            words = words.strip()
            if len(words) == 0:
                raise ValueError('Parameter words must not be empty')
            self.ssml_list.append('<amazon:effect name="whispered">%s</amazon:effect>' % self._escape(words))
        except AttributeError:
            raise AttributeError('Parameters words must be strings')

    def max_duration(self, max_duration,text,autobreaths= False):
        """Max duration"""
        if max_duration is None:
            raise TypeError('Parameter duration must not be None')
        self._validate_duration(max_duration)
        if autobreaths:
            self.ssml_list.append("<amazon:auto-breaths frequency='high' volume='medium' duration='medium'><prosody amazon:max-duration='%s'>%s</prosody></amazon:auto-breaths>" % (self._escape(max_duration),text))
        else:
            self.ssml_list.append("<prosody amazon:max-duration='%s'>%s</prosody>" % (self._escape(max_duration), text))
