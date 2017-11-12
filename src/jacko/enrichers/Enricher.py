#!/usr/bin/python

from abc import ABCMeta, abstractmethod


class Enricher(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def enrich(self, obj):
        raise NotImplementedError("Please implement this method")

    @classmethod
    def __subclasshook__(cls, C):
        if cls is Enricher:
            if any("enrich" in B.__dict__ for B in C.__mro__):
                return True
        return NotImplemented
