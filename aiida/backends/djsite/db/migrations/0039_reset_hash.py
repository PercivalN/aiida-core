# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=invalid-name,too-few-public-methods
"""
Invalidating node hash - User should rehash nodes for caching
"""
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

# Remove when https://github.com/PyCQA/pylint/issues/1931 is fixed
# pylint: disable=no-name-in-module,import-error
from django.db import migrations
from aiida.backends.djsite.db.migrations import upgrade_schema_version
from aiida.cmdline.utils.echo import echo_warning

REVISION = '1.0.39'
DOWN_REVISION = '1.0.38'

# Currently valid hash key
_HASH_EXTRA_KEY = '_aiida_hash'


def notify_user(apps, schema_editor):  # pylint: disable=unused-argument
    echo_warning("Invalidating all the hashes of all the nodes. Please run verdi rehash", bold=True)


class Migration(migrations.Migration):
    """Invalidating node hash - User should rehash nodes for caching"""

    dependencies = [
        ('db', '0038_data_migration_legacy_job_calculations'),
    ]

    operations = [
        migrations.RunPython(notify_user, reverse_code=notify_user),
        migrations.RunSQL(
            """UPDATE db_dbnode SET extras = extras #- '{""" + _HASH_EXTRA_KEY + """}'::text[];""",
            reverse_sql="""UPDATE db_dbnode SET extras = extras #- '{""" + _HASH_EXTRA_KEY + """}'::text[];"""),
        upgrade_schema_version(REVISION, DOWN_REVISION)
    ]
