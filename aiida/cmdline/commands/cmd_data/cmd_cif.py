# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi data cif` command."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from six.moves import range

import click

from aiida.cmdline.commands.cmd_data import verdi_data
from aiida.cmdline.commands.cmd_data import cmd_show
from aiida.cmdline.commands.cmd_data.cmd_export import data_export, export_options
from aiida.cmdline.commands.cmd_data.cmd_list import data_list, list_options
from aiida.cmdline.params import arguments, options, types
from aiida.cmdline.utils import decorators, echo

LIST_PROJECT_HEADERS = ['Id', 'Formulae', 'Source.URI']
EXPORT_FORMATS = ['cif']
VISUALIZATION_FORMATS = ['jmol', 'vesta']


@verdi_data.group('cif')
def cif():
    """Manipulation of CIF data objects."""


@cif.command('list')
@options.FORMULA_MODE()
@list_options
@decorators.with_dbenv()
def cif_list(raw, formula_mode, past_days, groups, all_users):
    """List store CifData objects."""
    from aiida.orm import CifData
    from tabulate import tabulate

    elements = None
    elements_only = False

    entry_list = data_list(CifData, LIST_PROJECT_HEADERS, elements, elements_only, formula_mode, past_days, groups,
                           all_users)

    counter = 0
    cif_list_data = list()

    if not raw:
        cif_list_data.append(LIST_PROJECT_HEADERS)
    for entry in entry_list:
        for i, value in enumerate(entry):
            if isinstance(value, list):
                new_entry = list()
                for elm in value:
                    if elm is None:
                        new_entry.append('')
                    else:
                        new_entry.append(elm)
                entry[i] = ",".join(new_entry)
        for i in range(len(entry), len(LIST_PROJECT_HEADERS)):
            entry.append(None)
        counter += 1
    cif_list_data.extend(entry_list)
    if raw:
        echo.echo(tabulate(cif_list_data, tablefmt='plain'))
    else:
        echo.echo(tabulate(cif_list_data, headers='firstrow'))
        echo.echo('\nTotal results: {}\n'.format(counter))


@cif.command('show')
@arguments.DATA(type=types.DataParamType(sub_classes=('aiida.data:cif',)))
@options.VISUALIZATION_FORMAT(type=click.Choice(VISUALIZATION_FORMATS), default='jmol')
@decorators.with_dbenv()
def cif_show(data, fmt):
    """Visualize CifData objects."""
    try:
        show_function = getattr(cmd_show, '_show_{}'.format(fmt))
    except AttributeError:
        echo.echo_critical('visualization format {} is not supported'.format(fmt))

    show_function(fmt, data)


@cif.command('content')
@arguments.DATA(type=types.DataParamType(sub_classes=('aiida.data:cif',)))
@decorators.with_dbenv()
def cif_content(data):
    """Show the content of the file behind CifData objects."""
    for node in data:
        try:
            echo.echo(node.get_content())
        except IOError as exception:
            echo.echo_warning('could not read the content for CifData<{}>: {}'.format(node.pk, str(exception)))


@cif.command('export')
@arguments.DATUM(type=types.DataParamType(sub_classes=('aiida.data:cif',)))
@options.EXPORT_FORMAT(type=click.Choice(EXPORT_FORMATS), default='cif')
@export_options
@decorators.with_dbenv()
def cif_export(**kwargs):
    """Export CifData object."""
    node = kwargs.pop('datum')
    output = kwargs.pop('output')
    fmt = kwargs.pop('fmt')
    force = kwargs.pop('force')

    kwargs = {k: v for k, v in kwargs.items() if v is not None}

    data_export(node, output, fmt, other_args=kwargs, overwrite=force)


@cif.command('import')
@click.argument('filename', type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@decorators.with_dbenv()
def cif_import(filename):
    """Import structure into CifData object."""
    from aiida.orm import CifData

    try:
        node, _ = CifData.get_or_create(filename)
        echo.echo_success('imported {}'.format(str(node)))
    except ValueError as err:
        echo.echo_critical(err)
