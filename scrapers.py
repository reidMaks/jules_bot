from abc import abstractmethod
import requests
import logging

from bs4 import BeautifulSoup

from irregular_verbs import IrregularVerb, Word


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)


def _strp(td):
    return td.get_text().strip()


class Scraper:
    host = "https://example.com"
    session = requests.Session()

    def __init__(self) -> None:
        super().__init__()

        self.data = self.session.get(self.resource).text
        self.soup = BeautifulSoup(self.data, features="html.parser")

    def __iter__(self):
        table = self.soup.find("table")
        self.trs = table.find_all("tr")[1:]
        return self

    def __next__(self):

        for tr in self.trs:
            tds = tr.find_all("td")

            translation = _strp(tds[3])
            infinitive = (_strp(tds[0]), self.get_pronunciation(tds[0]), translation)
            past_simple = (_strp(tds[1]), self.get_pronunciation(tds[1]), translation)
            past_participle = (
                _strp(tds[2]),
                self.get_pronunciation(tds[2]),
                translation,
            )

            del self.trs[0]
            return infinitive, past_simple, past_participle

        raise StopIteration

    @staticmethod
    @abstractmethod
    def get_pronunciation(td):
        pass


class NativeEnglishScraper(Scraper):
    host = "https://native-english.ru/"
    resource = f"{host}grammar/irregular-verbs"

    def get_pronunciation(self, td):
        pronunc_url_template = "{}audio/grammar/irregular-verbs/{}.mp3"
        return pronunc_url_template.format(self.host, td.find("span").get("data-word"))


class LingbaseScraper(Scraper):
    host = "https://lingbase.com/"
    resource = f"{host}ru/english/grammar/complete-list-of-irregular-verbs"

    def get_pronunciation(self, td):
        return f"{self.host}{td.find('audio').get('data-normal')[1:]}"
