import http.client
import logging
import random

from bs4 import BeautifulSoup
from telegram import Voice
from pydub import AudioSegment

from helpers import download_file, screen_text

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


def get_world_set_native_english():

    conn = http.client.HTTPSConnection("www.native-english.ru")

    conn.request("GET", "/grammar/irregular-verbs")
    res = conn.getresponse()
    data = res.read()
    soup = BeautifulSoup(data, features="html.parser")
    table = soup.find('table')
    irregular_set = []

    def get_pronunciation_url(td):
        pronunc_url_template = "https://www.native-english.ru/audio/grammar/irregular-verbs/{}.mp3"
        return pronunc_url_template.format(td.find('span').get('data-word'))

    for tr in table.find_all('tr')[1:]:
        tds = tr.find_all('td')
        translation = tds[3].get_text().strip()
        infinitive = Word(tds[0].get_text().strip(),
                          get_pronunciation_url(tds[0]), translation)
        past_simple = Word(tds[1].get_text().strip(),
                           get_pronunciation_url(tds[1]), translation)
        past_participle = Word(tds[2].get_text().strip(),
                               get_pronunciation_url(tds[2]),
                               translation)

        irregular_set.append(IrregularVerb(infinitive, past_simple,
                                           past_participle))

    return irregular_set


def get_world_set_lingbase():

    host = "lingbase.com"
    conn = http.client.HTTPSConnection(host)

    conn.request("GET", "/ru/english/grammar/complete-list-of-irregular-verbs")
    res = conn.getresponse()
    data = res.read()
    soup = BeautifulSoup(data, features="html.parser")
    table = soup.find('table')
    irregular_set = []

    def get_pronunciation_url(td):
        return f"https://lingbase.com{td.find('audio').get('data-normal')}"

    for tr in table.find_all('tr')[1:]:
        tds = tr.find_all('td')
        translation = tds[3].get_text().strip()
        infinitive = Word(tds[0].get_text().strip(),
                          get_pronunciation_url(tds[0]), translation)
        past_simple = Word(tds[1].get_text().strip(),
                           get_pronunciation_url(tds[1]), translation)
        past_participle = Word(tds[2].get_text().strip(),
                               get_pronunciation_url(tds[2]),
                               translation)

        irregular_set.append(IrregularVerb(infinitive, past_simple,
                                           past_participle))

    return irregular_set


class Word:
    def __init__(self, spelling: str, pronunciation: str,
                 translation: str) -> None:
        self.spelling = screen_text(spelling)
        self.pronunciation = pronunciation
        self.translation = screen_text(translation)

    def get_voice(self) -> Voice:
        file = download_file(self.pronunciation)
        ogg_file = AudioSegment.from_mp3(file).export(f'{file.stem}.ogg', format='ogg')
        song = AudioSegment.from_ogg(ogg_file.name)
        return song, ogg_file, f'{file.stem}.ogg', song.duration_seconds

    def __repr__(self) -> str:
        return f"en: {self.spelling} ru:{self.translation}"

    def __str__(self) -> str:
        return self.__repr__()


class IrregularVerb:
    def __init__(self, infinitive: Word, past_simple: Word,
                 past_participle: Word) -> None:
        self.infinitive = infinitive
        self.past_simple = past_simple
        self.past_participle = past_participle
        self.translation = infinitive.translation
        self.is_verb = True
        self.voice = None
        self.forms = ('infinitive', 'past_simple', 'past_participle')

    def get_voice(self):
        if self.voice is not None:
            logger.info(f'{self.infinitive.spelling} was picked up from cache')
            return (self.voice,)

        infinitive_voice, *_ = self.infinitive.get_voice()
        past_simple_voice, *_ = self.past_simple.get_voice()
        past_participle_voice, *_ = self.past_participle.get_voice()
        concatenated_voice = infinitive_voice + past_simple_voice + past_participle_voice
        file = concatenated_voice.export(f"full_{self.infinitive.spelling}.ogg",
                                         format="ogg", codec="libopus")
        return concatenated_voice, file, file.name, concatenated_voice.duration_seconds

    def get_spelling(self):
        return "\n".join(
                         [f"`infinitive      ` *{self.infinitive.spelling}*",
                          f"`past simple     ` *{self.past_simple.spelling}*",
                          f"`past participle ` *{self.past_participle.spelling}*",
                          f"`translation     ` *{self.infinitive.translation}*"])

    def __repr__(self) -> str:
        return f"{self.infinitive.spelling}-{self.past_simple.spelling}-{self.past_participle.spelling}"

    def __str__(self) -> str:
        return self.__repr__()
    
    def __eq__(self, other):
        return self.infinitive.spelling == other.infinitive.spelling


class IrregularVerbs:
    def __init__(self) -> None:
        
        try:
            self.verbs = get_world_set_native_english()
        except Exception as e:
            logger.exception("there are some issues with native_english")
        
        try:
            self.verbs_extended = [*self.verbs, *[x for x in get_world_set_lingbase() if x not in self.verbs]]
        except Exception as e:
            logger.exception("there are some issues with lingbase")

    def get_random_verb(self, extended=False) -> IrregularVerb:
        return random.choice(self.verbs if not extended else self.verbs_extended)

IrregularVerbsSet = IrregularVerbs()