import http.client
import logging
import random

from bs4 import BeautifulSoup
from telegram import Voice
from pydub import AudioSegment

from helpers import download_file, screen_text
from scrapers import LingbaseScraper, NativeEnglishScraper


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)


class Word:
    def __init__(self, spelling: str, pronunciation: str, translation: str) -> None:
        self.spelling = screen_text(spelling)
        self.pronunciation = pronunciation
        self.translation = screen_text(translation)

    def get_voice(self) -> Voice:
        file = download_file(self.pronunciation)
        ogg_file = AudioSegment.from_mp3(file).export(f"{file.stem}.ogg", format="ogg")
        song = AudioSegment.from_ogg(ogg_file.name)
        return song, ogg_file, f"{file.stem}.ogg", song.duration_seconds

    def __repr__(self) -> str:
        return f"en: {self.spelling} ru:{self.translation}"

    def __str__(self) -> str:
        return self.__repr__()


class IrregularVerb:
    def __init__(
        self, infinitive: Word, past_simple: Word, past_participle: Word
    ) -> None:
        self.infinitive = infinitive
        self.past_simple = past_simple
        self.past_participle = past_participle
        self.translation = infinitive.translation
        self.is_verb = True
        self.voice = None
        self.forms = ("infinitive", "past_simple", "past_participle")

    def get_voice(self):
        if self.voice is not None:
            logger.info(f"{self.infinitive.spelling} was picked up from cache")
            return (self.voice,)

        infinitive_voice, *_ = self.infinitive.get_voice()
        past_simple_voice, *_ = self.past_simple.get_voice()
        past_participle_voice, *_ = self.past_participle.get_voice()
        concatenated_voice = (
            infinitive_voice + past_simple_voice + past_participle_voice
        )
        file = concatenated_voice.export(
            f"full_{self.infinitive.spelling}.ogg", format="ogg", codec="libopus"
        )
        return concatenated_voice, file, file.name, concatenated_voice.duration_seconds

    def get_spelling(self):
        return "\n".join(
            [
                f"`infinitive      ` *{self.infinitive.spelling}*",
                f"`past simple     ` *{self.past_simple.spelling}*",
                f"`past participle ` *{self.past_participle.spelling}*",
                f"`translation     ` *{self.infinitive.translation}*",
            ]
        )

    def __repr__(self) -> str:
        return f"{self.infinitive.spelling}-{self.past_simple.spelling}-{self.past_participle.spelling}"

    def __str__(self) -> str:
        return self.__repr__()

    def __eq__(self, other):
        return self.infinitive.spelling == other.infinitive.spelling


class IrregularVerbs:
    def __init__(self) -> None:

        try:
            self.verbs = [
                IrregularVerb(Word(*i), Word(*s), Word(*p))
                for i, s, p in NativeEnglishScraper()
            ]
        except Exception as e:
            logger.exception("there are some issues with native_english")

        try:
            self.verbs_extended = [
                *self.verbs,
                *[
                    IrregularVerb(Word(*i), Word(*s), Word(*p))
                    for i, s, p in LingbaseScraper()
                ],
            ]
        except Exception as e:
            logger.exception("there are some issues with lingbase")

    def get_random_verb(self, extended=False) -> IrregularVerb:
        return random.choice(self.verbs if not extended else self.verbs_extended)


IrregularVerbsSet = IrregularVerbs()
