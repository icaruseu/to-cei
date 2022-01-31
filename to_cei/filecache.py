import os
import shelve
from pathlib import Path
from typing import Optional

import requests


class FileCache:
    __shelf: shelve.Shelf

    def __init__(self, base: str = str(Path.home().joinpath(".cache", "to-cei"))):
        if not os.path.isdir(base):
            os.makedirs(base)
        file = os.path.join(base, "cache")
        self.__shelf = shelve.open(file, writeback=True)

    def __exit__(self):
        self.__shelf.close()

    def get(self, url: str, force: bool = False) -> Optional[str]:
        if url not in self.__shelf or force == True:
            with requests.get(url) as response:
                self.__shelf[url] = response.text
                return response.text
        else:
            text = self.__shelf[url]
            assert isinstance(text, str)
            return text
