# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Utility functions for command line commands related to the daemon."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import click
from tabulate import tabulate

from aiida.cmdline.utils import echo
from aiida.cmdline.utils.common import format_local_time

_START_CIRCUS_COMMAND = 'start-circus'


def print_client_response_status(response):
    """
    Print the response status of a call to the CircusClient through the DaemonClient

    :param response: the response object
    """
    from aiida.engine.daemon.client import DaemonClient

    if 'status' not in response:
        return

    if response['status'] == 'active':
        click.secho('RUNNING', fg='green', bold=True)
    elif response['status'] == 'ok':
        click.secho('OK', fg='green', bold=True)
    elif response['status'] == DaemonClient.DAEMON_ERROR_NOT_RUNNING:
        click.secho('FAILED', fg='red', bold=True)
        click.echo('Try to run \'verdi daemon start --foreground\' to potentially see the exception')
    elif response['status'] == DaemonClient.DAEMON_ERROR_TIMEOUT:
        click.secho('TIMEOUT', fg='red', bold=True)
    else:
        click.echo(response['status'])


def get_daemon_status(client):
    """
    Print the status information of the daemon for a given profile through its DaemonClient

    :param client: the DaemonClient
    """

    if not client.is_daemon_running:
        return 'The daemon is not running'

    status_response = client.get_status()

    if status_response['status'] == 'stopped':
        return 'The daemon is paused'

    if status_response['status'] == 'error':
        return 'The daemon is in an unexpected state, try verdi daemon restart --reset'

    if status_response['status'] == 'timeout':
        return 'The daemon is running but the call to the circus controller timed out'

    worker_response = client.get_worker_info()
    daemon_response = client.get_daemon_info()

    if 'info' not in worker_response or 'info' not in daemon_response:
        return 'Call to the circus controller timed out'

    workers = [['PID', 'MEM %', 'CPU %', 'started']]
    for worker_pid, worker_info in worker_response['info'].items():
        worker_row = [worker_pid, worker_info['mem'], worker_info['cpu'], format_local_time(worker_info['create_time'])]
        workers.append(worker_row)

    if len(workers) > 1:
        workers_info = tabulate(workers, headers='firstrow', tablefmt='simple')
    else:
        workers_info = '--> No workers are running. Use verdi daemon incr to start some!\n'

    info = {
        'pid': daemon_response['info']['pid'],
        'time': format_local_time(daemon_response['info']['create_time']),
        'nworkers': len(workers) - 1,
        'workers': workers_info
    }

    template = ('Daemon is running as PID {pid} since {time}\nActive workers [{nworkers}]:\n{workers}\n'
                'Use verdi daemon [incr | decr] [num] to increase / decrease the amount of workers')

    return template.format(**info)


def delete_stale_pid_file(client):
    """Delete a potentially state daemon PID file.

    Checks if the PID contatined in the circus PID file (circus-{PROFILE_NAME}.pid) matches a valid running `verdi`
    process. If it does not, the PID file is stale and will be removed.

    This situation can arise if a system is shut down suddenly and so the process is killed but the PID file is not
    deleted in time. When the `get_daemon_pid()` method is called, an incorrect PID is returned. Alternatively, another
    process or the user may have meddled with the PID file in some way, corrupting it.

    :param client: the `DaemonClient`
    """
    import os
    import psutil

    class StartCircusNotFound(Exception):
        """For when 'start-circus' is not found in the ps command."""

    pid = client.get_daemon_pid()

    if pid is not None:
        try:
            process = psutil.Process(pid)
            if _START_CIRCUS_COMMAND not in process.cmdline():
                raise StartCircusNotFound()  # Also this is a case in which the process is not there anymore
        except (psutil.AccessDenied, psutil.NoSuchProcess, StartCircusNotFound):
            echo.echo_warning(
                'Deleted apparently stale daemon PID file as its associated process<{}> does not exist anymore'.format(
                    pid))
            if os.path.isfile(client.circus_pid_file):
                os.remove(client.circus_pid_file)
