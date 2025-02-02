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
Translator for calculation node
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import os

from aiida.restapi.translator.nodes.node import NodeTranslator
from aiida.restapi.common.exceptions import RestInputValidationError
from aiida.orm.utils.repository import FileType


class CalculationTranslator(NodeTranslator):
    """
    Translator relative to resource 'calculations' and aiida class Calculation
    """

    # A label associated to the present class (coincides with the resource name)
    __label__ = "calculations"
    # The AiiDA class one-to-one associated to the present class
    from aiida.orm import CalculationNode
    _aiida_class = CalculationNode
    # The string name of the AiiDA class
    _aiida_type = "process.calculation.calculation.CalculationNode"

    _result_type = __label__

    def __init__(self, **kwargs):
        """
        Initialise the parameters.
        Create the basic query_help
        """
        # basic query_help object
        super(CalculationTranslator, self).__init__(Class=self.__class__, **kwargs)

        ## calculation schema
        # All the values from column_order must present in additional info dict
        # Note: final schema will contain details for only the fields present in column order
        self._schema_projections = {
            "column_order": [
                "id", "label", "node_type", "ctime", "mtime", "uuid", "user_id", "user_email", "attributes.state",
                "attributes", "extras"
            ],
            "additional_info": {
                "id": {
                    "is_display": True
                },
                "label": {
                    "is_display": False
                },
                "node_type": {
                    "is_display": True
                },
                "ctime": {
                    "is_display": True
                },
                "mtime": {
                    "is_display": True
                },
                "uuid": {
                    "is_display": False
                },
                "user_id": {
                    "is_display": False
                },
                "user_email": {
                    "is_display": True
                },
                "attributes.state": {
                    "is_display": True
                },
                "attributes": {
                    "is_display": False
                },
                "extras": {
                    "is_display": False
                }
            }
        }

    @staticmethod
    def get_files_list(node_obj, dir_obj=None, files=None, prefix=None):
        """
        Return the list of all files contained in the node object repository
        If a directory object `dir_obj` of the repository is passed, get the list of all files
        recursively in the specified directory

        :param node_obj: node object
        :param dir_obj: directory in which files will be searched
        :param files: list of files if any
        :param prefix: file name prefix if any
        :return: the list of files
        """
        if files is None:
            files = []
        if prefix is None:
            prefix = []

        if dir_obj:
            flist = node_obj.list_objects(dir_obj)
        else:
            flist = node_obj.list_objects()

        for fname, ftype in flist:
            if ftype == FileType.FILE:
                filename = os.path.join(*(prefix + [fname]))
                files.append(filename)
            elif ftype == FileType.DIRECTORY:
                CalculationTranslator.get_files_list(node_obj, fname, files, prefix + [fname])
        return files

    @staticmethod
    def get_retrieved_inputs(node, filename=None, rtype=None):
        """
        Get the submitted input files for job calculation
        :param node: aiida node
        :return: the retrieved input files for job calculation
        """
        if node.node_type.startswith("process.calculation.calcjob"):

            if filename is not None:
                response = {}

                if rtype is None:
                    rtype = "download"

                if rtype == "download":
                    try:
                        content = node.get_object_content(filename)
                    except IOError:
                        error = "Error in getting {} content".format(filename)
                        raise RestInputValidationError(error)

                    response["status"] = 200
                    response["data"] = content
                    response["filename"] = filename.replace("/", "_")

                else:
                    raise RestInputValidationError("rtype is not supported")

                return response

            # if filename is not provided, return list of all retrieved files
            retrieved = CalculationTranslator.get_files_list(node)
            return retrieved

        return []

    @staticmethod
    def get_retrieved_outputs(node, filename=None, rtype=None):
        """
        Get the retrieved output files for job calculation
        :param node: aiida node
        :return: the retrieved output files for job calculation
        """
        if node.node_type.startswith("process.calculation.calcjob"):

            retrieved_folder_node = node.outputs.retrieved
            response = {}

            if retrieved_folder_node is None:
                response["status"] = 200
                response["data"] = "This node does not have retrieved folder"
                return response

            if filename is not None:

                if rtype is None:
                    rtype = "download"

                if rtype == "download":
                    try:
                        content = retrieved_folder_node.get_object_content(filename)
                    except IOError:
                        error = "Error in getting {} content".format(filename)
                        raise RestInputValidationError(error)

                    response["status"] = 200
                    response["data"] = content
                    response["filename"] = filename.replace("/", "_")

                else:
                    raise RestInputValidationError("rtype is not supported")

                return response

            # if filename is not provided, return list of all retrieved files
            retrieved = CalculationTranslator.get_files_list(retrieved_folder_node)
            return retrieved

        return []
