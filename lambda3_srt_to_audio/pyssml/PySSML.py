""" PySSML is a helper to construct Amazon Alexa SSML

1. Create a PySSML object
    s = PySSML()

2. Add your speech text
    s.say('Hello')

3. Retrieve your SSML
    s.ssml()      # to retrieve ssml with <speak> wrapper
    s.ssml(True)  # to retrieve ssml without <speak> wrapper
    s.to_object() # to retrieve complete speach output object

"""
import re
import urllib.parse


class PySSML:
    INTERPRET_AS = ['characters', 'cardinal', 'number', 'ordinal', 'digits', 'fraction',
                    'unit', 'date', 'time', 'telephone', 'address']

    DATE_FORMAT = ['mdy', 'dmy', 'ymd', 'md', 'dm', 'ym', 'my', 'd', 'm', 'y']

    ROLE = ['ivona:VB', 'ivona:VBD', 'ivona:NN', 'ivona:SENSE_1']

    IPA_CONSONANTS = ['b', 'd', 'd͡ʒ', 'ð', 'f', 'g', 'h', 'j', 'k', 'l', 'm', 'n', 'ŋ',
                      'p', 'ɹ', 's', 'ʃ', 't', 't͡ʃ', 'θ', 'v', 'w', 'z', 'ʒ']

    IPA_VOWELS = ['ə', 'ɚ', 'æ', 'aɪ', 'aʊ', 'ɑ', 'eɪ', 'ɝ', 'ɛ', 'i', 'ɪ', 'oʊ', 'ɔ', '',
                  'ɔɪ', 'u', 'ʊ', 'ʌ']

    X_SAMPA_CONSONANTS = ['b', 'd', 'dZ', 'D', 'f', 'g', 'h', 'j', 'k', 'l', 'm', 'n', 'N', 'p', 'r\\',
                          's', 'S', 't', 'tS', 'T', 'v', 'w', 'z', 'Z']

    X_SAMPA_VOWELS = ['@', '@`', '{', 'aI', 'aU', 'A', 'eI', '3`', 'E', 'i', 'I', 'oU', 'O', 'OI', 'U',
                      'U', 'V']

    IPA_SPECIAL = ['ˈ', 'ˌ', '.']

    X_SAMPA_SPECIAL = ['”', '%', '.']

    ALPHABETS = {
        'ipa': IPA_CONSONANTS + IPA_VOWELS + IPA_SPECIAL,
        'x-sampa': X_SAMPA_CONSONANTS + X_SAMPA_VOWELS + X_SAMPA_SPECIAL
    }

    PAUSE_STRENGTH = ['none', 'x-weak', 'weak', 'medium', 'strong', 'x-strong']

    EMPHASIS_LEVELS = ['strong', 'moderate', 'reduced']

    PROSODY_ATTRIBUTES = {
        'rate': ['x-slow', 'slow', 'medium', 'fast', 'x-fast'],
        'pitch': ['x-low', 'low', 'medium', 'high', 'x-high'],
        'volume': ['silent', 'x-soft', 'soft', 'medium', 'loud', 'x-loud']
    }

    def __init__(self):
        self.ssml_list = []
        self.card_list = []

    def clear(self):
        self.ssml_list = []
        self.card_list = []

    def _escape(self, text):
        return re.sub('&', 'and', re.sub('[\<\>\"\']', '', str(text)))

    def _validate_duration(self, duration):
        try:
            matches = re.match('^(\d*\.?\d+)(s|ms)$', duration)
            value_part = int(matches.groups()[0])
            unit_part = matches.groups()[1]
            if (unit_part == 's' and value_part > 10) or value_part > 10000:
                raise ValueError('Duration %s is longer than 10 seconds' % duration)
        except Exception:
            raise ValueError('Duration %s is invalid' % duration)

    def _validate_url(self, url):
        try:
            parse_tokens = urllib.parse.urlparse(url)
            if parse_tokens[0] == '' or parse_tokens[1] == '':
                raise ValueError('URL %s invalid' % url)
        except Exception:
            raise ValueError('URL %s invalid' % url)

    def dump(self):
        """Dump a list of all items added to ssml_list object"""
        for item in self.ssml_list:
            print(item)

    def to_object(self):
        """Return an Alexa speech output object"""
        return {'type': 'SSML', 'speech': self.ssml()}

    def ssml(self, old_method=False):
        """Return the SSML, pass true to strip <speak> tag wrapper"""
        result = ' '.join(self.ssml_list)
        return result if old_method else '<speak>%s</speak>' % result

    def card(self):
        return ' '.join(self.card_list)

    def say(self, text):
        """Add raw text to SSML"""
        if text is None:
            raise TypeError('Parameter text must not be None')
        self.ssml_list.append('%s' % self._escape(text))
        self.card_list.append('%s' % self._escape(text))

    def say_with_mark(self, text,mark_name_begin,mark_name_end):
        """Max duration"""
        if mark_name_begin is None or mark_name_end is None or text is None:
            raise TypeError('mark_name or text must not be None')
        self.ssml_list.append("<mark name='%s'/>%s<mark name='%s'/>" % (mark_name_begin,self._escape(text),mark_name_end))
        self.card_list.append("<mark name='%s'/>%s<mark name='%s'/>" % (mark_name_begin, self._escape(text), mark_name_end))

    def say_with_mark_max_duration(self, text,mark_name_begin,mark_name_end,max_duration):
        """Max duration"""
        if mark_name_begin is None or mark_name_end is None or text is None:
            raise TypeError('mark_name or text must not be None')
        self.ssml_list.append("<mark name='%s'/><prosody amazon:max-duration='%s'>%s</prosody><mark name='%s'/>" % (mark_name_begin,self._escape(max_duration),self._escape(text),mark_name_end))
        self.card_list.append("<mark name='%s'/><prosody amazon:max-duration='%s'>%s</prosody><mark name='%s'/>" % (mark_name_begin, self._escape(max_duration),self._escape(text), mark_name_end))


    def paragraph(self, text):
        """Wrap text with <p> tag"""
        if text is None:
            raise TypeError('Parameter text must not be None')
        self.ssml_list.append('<p>%s</p>' % self._escape(text))
        self.card_list.append('\n%s\n' % self._escape(text))

    def sentence(self, text):
        """Wrap text with <s> tag"""
        if text is None:
            raise TypeError('Parameter text must not be None')
        self.ssml_list.append('<s>%s</s>' % self._escape(text))
        self.card_list.append('%s ' % self._escape(text))

    def pause(self, duration):
        """Add a pause to SSML, must be between 0 and 10 seconds"""
        if duration is None:
            raise TypeError('Parameter duration must not be None')
        self._validate_duration(duration)
        self.ssml_list.append("<break time='%s'/>" % self._escape(duration))

    def pause_by_strength(self, strength):
        if strength is None:
            raise TypeError('Parameter strength must not be None')
        try:
            strength = strength.lower().strip()
        except AttributeError:
            raise AttributeError('Parameter strength must be a string')
        if strength in PySSML.PAUSE_STRENGTH:
            self.ssml_list.append("<break strength='%s'/>" % strength)
        else:
            raise ValueError('Value %s is not a valid strength' % strength)

    def audio(self, url):
        """Add audio to SSML, must pass a valid url"""
        if url is None:
            raise TypeError('Parameter url must not be None')
        self._validate_url(url)
        self.ssml_list.append("<audio src='%s'/>" % self._escape(url))

    def spell(self, text):
        """Read out each character in text"""
        if text is None:
            raise TypeError('Parameter text must not be None')
        self.ssml_list.append("<say-as interpret-as='spell-out'>%s</say-as>" % self._escape(text))
        self.card_list.append('%s' % self._escape(text))

    def spell_slowly(self, text, duration):
        """Read out each character in text slowly placing a pause between characters, pause between 0 and 10 seconds"""
        if text is None:
            raise TypeError('Parameter text must not be None')
        if duration is None:
            raise TypeError('Parameter duration must not be None')
        self._validate_duration(duration)
        ssml = ''
        for c in self._escape(text):
            ssml += "<say-as interpret-as='spell-out'>%s</say-as> <break time='%s'/> " % (c, self._escape(duration))
        self.ssml_list.append(ssml.strip())
        self.card_list.append('%s' % self._escape(text))

    def say_as(self, word, interpret, interpret_format=None):
        """Special considerations when speaking word include date, numbers, etc."""
        if word is None:
            raise TypeError('Parameter word must not be None')
        if interpret is None:
            raise TypeError('Parameter interpret must not be None')
        if interpret not in PySSML.INTERPRET_AS:
            raise ValueError('Unknown interpret as %s' % str(interpret))
        if interpret_format is not None and interpret_format not in PySSML.DATE_FORMAT:
            raise ValueError('Unknown date format %s' % str(interpret_format))
        if interpret_format is not None and interpret != 'date':
            raise ValueError('Date format %s not valid for interpret as %s' % (str(interpret_format), str(interpret)))
        format_ssml = '' if interpret_format is None else " format='%s'" % interpret_format
        self.ssml_list.append(
            "<say-as interpret-as='%s'%s>%s</say-as>" % (interpret, format_ssml, str(word)))
        self.card_list.append('%s' % self._escape(word))

    def parts_of_speech(self, word, role):
        """Special considerations when speaking word include usage or role of word"""
        if word is None:
            raise TypeError('Parameter word must not be None')
        if role is None:
            raise TypeError('Parameter role must not be None')
        if role not in PySSML.ROLE:
            raise ValueError('Unknown role %s' % str(role))
        self.ssml_list.append("<w role='%s'>%s</w>" % (self._escape(role), self._escape(word)))
        self.card_list.append('%s' % self._escape(word))

    def phoneme(self, word, alphabet, ph):
        """Specify specific phonetics used when speaking word"""
        if word is None:
            raise TypeError('Parameter word must not be None')
        if alphabet is None:
            raise TypeError('Parameter alphabet must not be None')
        if ph is None:
            raise TypeError('Parameter ph must not be None')
        if alphabet not in PySSML.ALPHABETS:
            raise ValueError('Unknown alphabet %s' % str(alphabet))
        self.ssml_list.append(
            "<phoneme alphabet='%s' ph='%s'>%s</phoneme>" % (
                self._escape(alphabet), self._escape(ph), self._escape(word)))
        self.card_list.append('%s' % self._escape(word))

    def emphasis(self, level, word):
        if level is None:
            raise TypeError('Parameter level must not be None')
        if word is None:
            raise TypeError('Parameter word must not be None')
        try:
            if len(word.strip()) == 0:
                raise ValueError('Parameter word must not be empty')
            level = level.lower().strip()
            if level in PySSML.EMPHASIS_LEVELS:
                self.ssml_list.append("<emphasis level='%s'>%s</emphasis>" % (level, self._escape(word)))
            else:
                raise ValueError('Unknown emphasis level %s' % level)
        except AttributeError:
            raise AttributeError('Parameters must be strings')

    def prosody(self, attributes, word):
        tag_attributes = ''
        if attributes is None:
            raise TypeError('Parameter attributes must not be None')
        if word is None:
            raise TypeError('Parameter word must not be None')
        try:
            for k, v in attributes.items():
                # v = v.lower().strip()
                if v in PySSML.PROSODY_ATTRIBUTES[k]:
                    tag_attributes += " %s='%s'" % (k, v)
                elif k == 'rate':
                    # rate_value = int(''.join([c for c in v if c in '0123456789']))
                    if 20.0 <= v <= 200.0:
                        tag_attributes += " %s='%f%%'" % (k, v)
                    else:
                        raise ValueError('Attribute %s value %s is invalid' % (v, k))
                else:
                    raise ValueError('Attribute %s value %s is invalid' % (v, k))
            self.ssml_list.append("<prosody%s>%s</prosody>" % (tag_attributes, self._escape(word)))
        except AttributeError:
            raise AttributeError('Parameters must be strings')
        except KeyError:
            raise KeyError('Attribute is unknown')
        except ValueError:
            raise ValueError('Attribute value is invalid')

    def sub(self, alias, word):
        if alias is None:
            raise TypeError('Parameter alias must not be None')
        if word is None:
            raise TypeError('Parameter word must not be None')
        try:
            alias = alias.strip()
            if len(alias) == 0:
                raise ValueError('Alias must not be empty')
            word = word.strip()
            if len(word) == 0:
                raise ValueError('Word must not be empty')
            self.ssml_list.append("<sub alias='%s'>%s</sub>" % (alias, self._escape(word)))
        except AttributeError:
            raise AttributeError('Parameters alias and word must be strings')