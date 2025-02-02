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
Translator for data node
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from aiida.restapi.translator.nodes.node import NodeTranslator


class DataTranslator(NodeTranslator):
    """
    Translator relative to resource 'data' and aiida class `~aiida.orm.nodes.data.data.Data`
    """

    # A label associated to the present class (coincides with the resource name)
    __label__ = "data"
    # The AiiDA class one-to-one associated to the present class
    from aiida.orm import Data
    _aiida_class = Data
    # The string name of the AiiDA class
    _aiida_type = "data.Data"

    _result_type = __label__

    def __init__(self, Class=None, **kwargs):
        """
        Initialise the parameters.
        Create the basic query_help
        """

        # Assume default class is this class (cannot be done in the
        # definition as it requires self)
        if Class is None:
            Class = self.__class__

        super(DataTranslator, self).__init__(Class=Class, **kwargs)
