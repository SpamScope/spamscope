#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copyright 2016 Fedele Mantuano (https://twitter.com/fedelemantuano)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from abc import ABCMeta, abstractmethod


class ScoreOutOfRange(ValueError):
    pass


class PropertyDoesNotExists(Exception):
    pass


class BitMapNotDefined(ValueError):
    pass


class BitMapNotValid(ValueError):
    pass


class ScoreNotInteger(TypeError):
    pass


class BitMap(object):
    """Abstract class to make bitmap, to give
    custom score to the properties of object.
    """

    __metaclass__ = ABCMeta

    _map_name = "abstract"

    def __init__(self):
        self.define_bitmap()
        if not hasattr(self, "_bitmap"):
            raise BitMapNotDefined(
                "Bitmap for {} not defined.".format(self.map_name))

        self._valide_bitmap()
        self.reset_score()

    @abstractmethod
    def define_bitmap(self):
        """This method define the bitmap of object.
        Every property has a bit position: 0 is low significant bit,
        then low significant property, etc
        Fill all positions from 0 to max.

        Example:

            self._bitmap = {
                "property_1": 0,
                "property_2": 1,
                "property_3": 2,
            }

        """
        pass

    def _valide_bitmap(self):
        """Check if bitmap has a valid format. """

        if not isinstance(self.bitmap, dict):
            raise BitMapNotValid(
                "BitMap must be a dict, {} given".format(
                    type(self.bitmap)))

        bitmap_values = set(self.bitmap.values())
        expected_values = set(range(0, len(self.bitmap)))

        if (bitmap_values - expected_values):
            raise BitMapNotValid("BitMap not valid. Fill all the range")

    def reset_score(self):
        """Reset the total score. """

        self.score = 0

    def unset_property_score(self, *args):
        """Remove from score the given properties. """

        for p in args:
            if p not in self.bitmap:
                raise PropertyDoesNotExists(
                    "Property {!r} does not exists".format(p))

            value = self.bitmap.get(p)

            # New score
            self._score &= ~(1 << value)

    def set_property_score(self, *args):
        """Add to score the given properties. """

        for p in args:
            if p not in self.bitmap:
                raise PropertyDoesNotExists(
                    "Property {!r} does not exists".format(p))

            value = self.bitmap.get(p)

            # New score
            self._score |= (1 << value)

    def calculate_score(self, *args):
        """Return the score of given properties. """

        score = 0
        for p in args:
            if p not in self.bitmap:
                raise PropertyDoesNotExists(
                    "Property {!r} does not exists".format(p))

            value = self.bitmap.get(p)

            score |= (1 << value)

        return score

    def get_score_sum(self, *args):
        """Given a list of scores (Example: 2, 1, 0),
        the method outputs the sum of the bitmask.

        Example: 2^2 + 2^1 + 2^0 = 7

        """

        score_sum = 0
        for score in args:
            if not isinstance(score, int):
                raise ScoreNotInteger(
                    "Score {!r} is not a integer".format(score))
            score_sum |= (1 << score)

        return score_sum

    @property
    def bitmap(self):
        """Return bitmap dict (property: score). """

        return self._bitmap

    @property
    def map_name(self):
        """Return mapping name. """

        return self._map_name

    @map_name.setter
    def map_name(self, value):
        """Set mapping name. """

        self._map_name = value

    @property
    def score(self):
        """Return actual total score. """

        return self._score

    @score.setter
    def score(self, value):
        """Set score to value. """

        threshold = (1 << len(self.bitmap)) - 1
        if value > threshold:
            raise ScoreOutOfRange(
                "{} can only have values in the range [0, {}]".format(
                    self.map_name, threshold))

        self._score = value

    @property
    def score_properties(self):
        """Return the property labels of actual score,
        from high significant bit to low significant bit
        """

        properties = list()

        for k, v in self.bitmap.iteritems():
            if self.score & (1 << v):
                properties.append(k)

        return list(reversed(properties))
