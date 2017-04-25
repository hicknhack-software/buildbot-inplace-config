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
    def remove_command(self):
        return ''

    @property
    def echo_command(self):
        return 'echo'

    @property
    def home_path_var(self):
        return ''


class BashWorkerCommands(WorkerCommands):
    @property
    def remove_command(self):
        return 'rm -f'

    @property
    def home_path_var(self):
        return '$HOME'


class CmdWorkerCommands(WorkerCommands):
    @property
    def remove_command(self):
        return 'del'

    @property
    def home_path_var(self):
        return '%HOMEPATH%'


def get_worker_commands(worker_info):
    worker = self.global_config.inplace_workers.named_get(self.getWorkerName())
    assert isinstance(worker_info, Worker)
    return BashWorkerCommands if worker_info.shell == 'bash' else CmdWorkerCommands()


def get_home_path_var():
    worker_commands = get_worker_commands(worker_info=worker_info)
    return worker_commands.home_path_var

def create_echo_command_string(BuildStep=step, output=''):
    worker_commands = get_worker_commands(output)
    return worker_commands.echo_command + " " + output


def create_delte_command_string(files=''):
    worker_commands = get_worker_commands(files)
    return worker_commands.remove_command + " " + files
