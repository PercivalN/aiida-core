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
This module contains tests for UpfData and UpfData related functions.
"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import errno
import tempfile
import shutil
import os

from aiida import orm
from aiida.backends.testbase import AiidaTestCase
from aiida.common.exceptions import ParsingError
from aiida.orm.nodes.data.upf import parse_upf


class TestUpfParser(AiidaTestCase):
    """Tests UPF version / element_name parser function."""

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super(TestUpfParser, cls).setUpClass(*args, **kwargs)
        filepath_base = os.path.abspath(os.path.join(__file__, os.pardir, os.pardir, os.pardir, 'fixtures', 'pseudos'))
        filepath_barium = os.path.join(filepath_base, 'Ba.pbesol-spn-rrkjus_psl.0.2.3-tot-pslib030.UPF')
        filepath_oxygen = os.path.join(filepath_base, 'O.pbesol-n-rrkjus_psl.0.1-tested-pslib030.UPF')
        cls.pseudo_barium = orm.UpfData(file=filepath_barium).store()
        cls.pseudo_oxygen = orm.UpfData(file=filepath_oxygen).store()

    def setUp(self):
        """Setup a temporary directory to store UPF files."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Destroy the temporary directory created."""
        try:
            shutil.rmtree(self.temp_dir)
        except OSError as exception:
            if exception.errno == errno.ENOENT:
                pass
            elif exception.errno == errno.ENOTDIR:
                os.remove(self.temp_dir)
            else:
                raise IOError(exception)

    def test_get_upf_groups(self):
        """Test the `UpfData.get_upf_groups` class method."""
        type_string = orm.GroupTypeString.UPFGROUP_TYPE.value
        label_01 = 'family_01'
        label_02 = 'family_02'

        user = orm.User(email='alternate@localhost').store()

        self.assertEqual(orm.UpfData.get_upf_groups(), [])

        # Create group with default user and add `Ba` pseudo
        family_01, _ = orm.Group.objects.get_or_create(label=label_01, type_string=type_string)
        family_01.add_nodes([self.pseudo_barium])
        family_01.store()

        self.assertEqual({group.label for group in orm.UpfData.get_upf_groups()}, {label_01})

        # Create group with different user and add `O` pseudo
        family_02, _ = orm.Group.objects.get_or_create(label=label_02, type_string=type_string, user=user)
        family_02.add_nodes([self.pseudo_oxygen])
        family_02.store()

        self.assertEqual({group.label for group in orm.UpfData.get_upf_groups()}, {label_01, label_02})

        # Filter on a given user
        self.assertEqual({group.label for group in orm.UpfData.get_upf_groups(user=user.email)}, {label_02})

        # Filter on a given element
        groups = {group.label for group in orm.UpfData.get_upf_groups(filter_elements='O')}
        self.assertEqual(groups, {label_02})

        # Filter on a given element and user
        groups = {group.label for group in orm.UpfData.get_upf_groups(filter_elements='O', user=user.email)}
        self.assertEqual(groups, {label_02})

        # Filter on element and user that should not match anything
        groups = {group.label for group in orm.UpfData.get_upf_groups(filter_elements='Ba', user=user.email)}
        self.assertEqual(groups, set([]))

    def test_upf_version_one(self):
        """Check if parsing for regular UPF file (version 1) succeeds."""

        upf_filename = "O.test_file_v1.UPF"
        # regular upf file version 1 header
        upf_contents = u"\n".join([
            "<PP_INFO>"
            "Human readable section is completely irrelevant for parsing!",
            "<PP_HEADER",
            "contents before element tag",
            "O                     Element",
            "contents following element tag",
            ">",
        ])
        path_to_upf = os.path.join(self.temp_dir, upf_filename)
        with open(path_to_upf, 'w') as upf_file:
            upf_file.write(upf_contents)
        # try to parse version / element name from UPF file contents
        parsed_data = parse_upf(path_to_upf, check_filename=True)
        # check that parsed data matches the expected one
        self.assertEqual(parsed_data['version'], '1')
        self.assertEqual(parsed_data['element'], 'O')

    def test_upf_version_two(self):
        """Check if parsing for regular UPF file (version 2) succeeds."""

        upf_filename = "Al.test_file_v2.UPF"
        # regular upf file version 2 header
        upf_contents = u"\n".join([
            "<UPF version=\"2.0.1\">",
            "Human readable section is completely irrelevant for parsing!",
            "<PP_HEADER",
            "contents before element tag",
            "element=\"Al\"",
            "contents following element tag",
            ">",
        ])
        path_to_upf = os.path.join(self.temp_dir, upf_filename)
        with open(path_to_upf, 'w') as upf_file:
            upf_file.write(upf_contents)
        # try to parse version / element name from UPF file contents
        parsed_data = parse_upf(path_to_upf, check_filename=True)
        # check that parsed data matches the expected one
        self.assertEqual(parsed_data['version'], '2.0.1')
        self.assertEqual(parsed_data['element'], 'Al')

    def test_additional_header_line(self):
        """Regression #2228: check if parsing succeeds if additional header line is present."""

        upf_filename = "Pt.test_file.UPF"
        # minimal contents required for parsing including additional header
        # file
        upf_contents = u"\n".join([
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>",
            "<UPF version=\"2.0.1\">",
            "Human readable section is completely irrelevant for parsing!",
            "<PP_HEADER",
            "contents before element tag",
            "element=\"Pt\"",
            "contents following element tag",
            ">",
        ])
        path_to_upf = os.path.join(self.temp_dir, upf_filename)
        with open(path_to_upf, 'w') as upf_file:
            upf_file.write(upf_contents)
        # try to parse version / element name from UPF file contents
        parsed_data = parse_upf(path_to_upf, check_filename=True)
        # check that parsed data matches the expected one
        self.assertEqual(parsed_data['version'], '2.0.1')
        self.assertEqual(parsed_data['element'], 'Pt')

    def test_check_filename(self):
        """Test built-in check for if file name matches element"""

        upf_filename = "Al.test_file.UPF"
        # upf file header contents
        upf_contents = u"\n".join([
            "<UPF version=\"2.0.1\">",
            "Human readable section is completely irrelevant for parsing!",
            "<PP_HEADER",
            "contents before element tag",
            "element=\"Pt\"",
            "contents following element tag",
            ">",
        ])
        path_to_upf = os.path.join(self.temp_dir, upf_filename)
        with open(path_to_upf, 'w') as upf_file:
            upf_file.write(upf_contents)
        # Check if parser raises the desired ParsingError
        with self.assertRaises(ParsingError):
            _ = parse_upf(path_to_upf, check_filename=True)

    def test_missing_element_upf_v2(self):
        """Test parsers exception on missing element name in UPF v2."""

        upf_filename = "Ab.test_file_missing_element_v2.UPF"
        # upf file header contents
        upf_contents = u"\n".join([
            "<UPF version=\"2.0.1\">",
            "Human readable section is completely irrelevant for parsing!",
            "<PP_HEADER",
            "contents before element tag",
            "element should be here but is missing",
            "contents following element tag",
            ">",
        ])
        path_to_upf = os.path.join(self.temp_dir, upf_filename)
        with open(path_to_upf, 'w') as upf_file:
            upf_file.write(upf_contents)
        # Check if parser raises the desired ParsingError
        with self.assertRaises(ParsingError):
            _ = parse_upf(path_to_upf, check_filename=True)

    def test_invalid_element_upf_v2(self):
        """Test parsers exception on invalid element name in UPF v2."""

        upf_filename = "Ab.test_file_invalid_element_v2.UPF"
        # upf file header contents
        upf_contents = u"\n".join([
            "<UPF version=\"2.0.1\">",
            "Human readable section is completely irrelevant for parsing!",
            "<PP_HEADER",
            "contents before element tag",
            "element=\"Ab\""
            "contents following element tag",
            ">",
        ])
        path_to_upf = os.path.join(self.temp_dir, upf_filename)
        with open(path_to_upf, 'w') as upf_file:
            upf_file.write(upf_contents)
        # Check if parser raises the desired ParsingError
        with self.assertRaises(ParsingError):
            _ = parse_upf(path_to_upf, check_filename=True)

    def test_missing_element_upf_v1(self):
        """Test parsers exception on missing element name in UPF v1."""

        upf_filename = "O.test_file_missing_element_v1.UPF"
        # upf file header contents
        upf_contents = u"\n".join([
            "<PP_INFO>"
            "Human readable section is completely irrelevant for parsing!",
            "<PP_HEADER",
            "contents before element tag",
            "element should be here but is missing",
            "contents following element tag",
            ">",
        ])
        path_to_upf = os.path.join(self.temp_dir, upf_filename)
        with open(path_to_upf, 'w') as upf_file:
            upf_file.write(upf_contents)
        # Check if parser raises the desired ParsingError
        with self.assertRaises(ParsingError):
            _ = parse_upf(path_to_upf, check_filename=True)

    def test_invalid_element_upf_v1(self):
        """Test parsers exception on invalid element name in UPF v1."""

        upf_filename = "Ab.test_file_invalid_element_v1.UPF"
        # upf file header contents
        upf_contents = u"\n".join([
            "<PP_INFO>"
            "Human readable section is completely irrelevant for parsing!",
            "<PP_HEADER",
            "contents before element tag",
            "Ab                     Element",
            "contents following element tag",
            ">",
        ])
        path_to_upf = os.path.join(self.temp_dir, upf_filename)
        with open(path_to_upf, 'w') as upf_file:
            upf_file.write(upf_contents)
        # Check if parser raises the desired ParsingError
        with self.assertRaises(ParsingError):
            _ = parse_upf(path_to_upf, check_filename=True)
