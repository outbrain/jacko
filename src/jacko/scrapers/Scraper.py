from abc import ABCMeta, abstractmethod


class Scraper(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def scrape(self):
        raise NotImplementedError("Please implement this method")

    @classmethod
    def __subclasshook__(cls, C):
        if cls is Scraper:
            if any("scrape" in B.__dict__ for B in C.__mro__):
                return True
        return NotImplemented
