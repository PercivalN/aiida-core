# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Classes for describing atomic orbitals.

Contains general Orbital class.
For subclasses of Orbital, see submodules.
"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from aiida.common.exceptions import ValidationError
from aiida.plugins.entry_point import get_entry_point_from_class


def validate_int(value):
    """
    Validate that the value is an int
    """
    try:
        conv_value = int(value)
    except ValueError:
        raise ValidationError("must be an int number")
    return conv_value


def validate_int_or_none(value):
    """
    Validate that the value is a int or is None
    """
    if value is None:
        return None
    return validate_int(value)


def validate_float(value):
    """
    Validate that the value is a float
    """
    try:
        conv_value = float(value)
    except ValueError:
        raise ValidationError("must be a float number")
    return conv_value


def validate_float_or_none(value):
    """
    Validate that the value is a float or is None
    """
    if value is None:
        return None
    return validate_float(value)


def validate_len3_list(value):
    """
    Validate that the value is a list of three floats
    """
    try:
        conv_value = list(float(i) for i in value)
        if len(conv_value) != 3:
            raise ValueError
    except (ValueError, TypeError):
        raise ValidationError("must be a list of three float number")
    return conv_value


def validate_len3_list_or_none(value):
    """
    Validate that the value is a list of three floats or is None
    """
    if value is None:
        return None
    return validate_len3_list(value)


class Orbital(object):  # pylint: disable=useless-object-inheritance
    """
    Base class for Orbitals. Can handle certain basic fields, their setting
    and validation. More complex Orbital objects should then inherit from
    this class

    :param position: the absolute position (three floats) units in angstrom
    :param x_orientation: x,y,z unit vector defining polar angle theta
                          in spherical coordinates unitless
    :param z_orientation: x,y,z unit vector defining azimuthal angle phi
                          in spherical coordinates unitless
    :param orientation_spin: x,y,z unit vector defining the spin orientation
                             unitless
    :param diffusivity: Float controls the radial term in orbital equation
                        units are reciprocal Angstrom.
    """
    # len-2 tuples, with name and validator function
    _base_fields_required = (('position', validate_len3_list),
                             #NOTE: _orbital_type is internally used to manage the orbital type
                            )

    # len-3 tuples, with (name, validator, default_value)
    # See how it is defined in the RealhydrogenOrbital class
    _base_fields_optional = tuple()

    def __init__(self, **kwargs):
        # This runs the validator as well
        self.set_orbital_dict(kwargs)

    def __repr__(self):
        return '<{}: {}>'.format(self.__class__.__name__, str(self))

    def _validate_keys(self, input_dict):
        """
        Checks all the input_dict and tries to validate them, to ensure
        that they have been properly set raises Exceptions indicating any
        problems that should arise during the validation

        :param input_dict: a dictionary of inputs
        :return: input_dict: the original dictionary with all validated kyes
                 now removed
        :return: validated_dict: a dictionary containing all the input keys
                 which have now been validated.
        """

        validated_dict = {}
        if '_orbital_type' in input_dict:
            raise ValidationError("You cannot manually set the _orbital_type")
        entry_point = get_entry_point_from_class(self.__class__.__module__, self.__class__.__name__)[1]
        if entry_point is None:
            raise ValidationError(
                "Unable to detect entry point for current class {}, maybe you did not register an entry point for it?".
                format(self.__class__))

        validated_dict['_orbital_type'] = entry_point.name

        for name, validator in self._base_fields_required:
            try:
                value = input_dict.pop(name)
            except KeyError:
                raise ValidationError("Missing required parameter '{}'".format(name))
            # This might raise ValidationError
            try:
                value = validator(value)
            except ValidationError as exc:
                raise exc.__class__("Error validating '{}': {}".format(name, str(exc)))
            validated_dict[name] = value

        for name, validator, default_value in self._base_fields_optional:
            try:
                value = input_dict.pop(name)
            except KeyError:
                value = default_value
            # This might raise ValidationError
            try:
                value = validator(value)
            except ValidationError as exc:
                raise exc.__class__("Error validating '{}': {}".format(name, str(exc)))
            validated_dict[name] = value

        if input_dict:
            raise ValidationError('Unknown keys: {}'.format(list(input_dict.keys())))
        return validated_dict

    def set_orbital_dict(self, init_dict):
        """
        Sets the orbital_dict, which can vary depending on the particular
        implementation of this base class.

        :param init_dict: the initialization dictionary
        """
        self._orbital_dict = self._validate_keys(init_dict)

    def get_orbital_dict(self):
        """
        returns the internal keys as a dictionary
        """
        return self._orbital_dict
