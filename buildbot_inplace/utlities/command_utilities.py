""" Buildbot inplace config
(C) Copyright 2015-2017 HicknHack Software GmbH

The original code can be found at:
https://github.com/hicknhack-software/buildbot-inplace-config

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

from ..worker import Worker


class WorkerCommands(dict):
    @property
    def remove(self):
        return ''

    @property
    def echo(self):
        return 'echo'


class BashWorkerCommands(WorkerCommands):
    @property
    def remove(self):
        return 'rm -f'


class CmdWorkerCommands(BashWorkerCommands):
    @property
    def remove(self):
        return 'del'


def get_worker_commands(worker_info):
    assert isinstance(worker_info, Worker)
    return BashWorkerCommands if worker_info.shell == 'bash' else CmdWorkerCommands()


def create_echo_command_string(output=''):
    worker_commands = get_worker_commands(output)
    return worker_commands.echo + " " + output


def create_delte_command_string(files=''):
    worker_commands = get_worker_commands(files)
    return worker_commands.remove + " " + files
