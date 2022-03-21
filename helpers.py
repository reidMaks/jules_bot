import os
import glob
import pathlib
from urllib.parse import urlparse
import http.client
import logging

logger = logging.getLogger(__name__)


def remove_audio_files():

    files = glob.glob('*.mp3') + glob.glob('*.ogg')

    for file in files:
        try:
            os.remove(file)
            logger.info(f'file {file} was removed' )
        except OSError:
            logger.exception(f"Error while deleting file : {file}")


def screen_text(text):
    symbols = '()-'
    for s in symbols:
        text = text.replace(s, f'\{s}')
    return text

def download_file(link: str) -> str:
    parse_result = urlparse(link)
    path = parse_result.path
    file_name = path.split('/')[-1]

    file = pathlib.Path(file_name)

    if file.is_file():
        return file

    conn = http.client.HTTPSConnection(parse_result.hostname)
    payload = ''
    headers = {
            'Connection': 'keep-alive',
            'Accept': '*/*',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'no-cors',
            'Sec-Fetch-Dest': 'audio',
            'Range': 'bytes=0-'
        }
    conn.request("GET", path, payload, headers)
    res = conn.getresponse()
    data = res.read()

    open(path.split('/')[-1], 'bw').write(data)
    logger.info(f'file {file} was downloaded' )
    return pathlib.Path(file_name)
