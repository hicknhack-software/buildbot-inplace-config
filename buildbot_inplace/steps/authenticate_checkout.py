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
from ..project import RepoCredential
from buildbot.steps.shellsequence import ShellSequence, ShellArg
from configured_step_mixin import ConfiguredStepMixin
from checkout import set_url_auth
from twisted.internet import defer


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


#
# def get_worker_commands(worker_info):
#     worker = self.global_config.inplace_workers.named_get(self.getWorkerName())
#     assert isinstance(worker_info, Worker)
#     return BashWorkerCommands if worker_info.shell == 'bash' else CmdWorkerCommands()
#
#
# def get_home_path_var():
#     worker_commands = get_worker_commands(worker_info=worker_info)
#     return worker_commands.home_path_var
#
#
# def create_echo_command_string(BuildStep=step, output=''):
#     worker_commands = get_worker_commands(output)
#     return worker_commands.echo_command + " " + output
#
#
# def create_delte_command_string(files=''):
#     worker_commands = get_worker_commands(files)
#     return worker_commands.remove_command + " " + files
#
#
# def create_authenticate_checkout_steps(project):
#     repo_credentials = project.repo_credentials
#     if not repo_credentials:
#         return [ShellCommand(name='Unauthorized.', command=['echo', 'Incomplete Authentication Supplied. Skipping.'])]
#     auth_commands = [
#         ShellCommand(name='Delete Git Credentials', command='rm  -f $HOME/.git-credentials'),
#         ShellCommand(name='Configure git store',
#                      command=['git', 'config', '--global', 'credential.helper', 'store'])
#     ]
#     for repo_credential in repo_credentials:
#         assert isinstance(repo_credential, RepoCredential)
#         if not repo_credential.url and not repo_credential.user and not repo_credential.password:
#             continue
#         auth_url = set_url_auth(git_url=repo_credential.url, user=repo_credential.user,
#                                 password=repo_credential.password)
#         auth_commands.append(ShellCommand(command='echo ' + auth_url + ' >> $HOME/.git-credentials',
#                                           name='Store Credentials for Url ' + auth_url))
#     return auth_commands


class AuthenticateCheckoutStep(ShellSequence, ConfiguredStepMixin):
    def __init__(self, project=None, **kwargs):
        self.project = project
        self.descriptionDone = u'Authentication finished!'
        ShellSequence.__init__(self, commands=[], **kwargs)

    def run(self):
        repo_credentials = self.project.repo_credentials
        if not repo_credentials:
            self.commands.append(ShellArg(command='echo'))

        else:
            self.commands.extend([ShellArg('rm -f $HOME/.git-credentials'),
                                 ShellArg('git config --global credential.helper store')])

            for repo_credential in repo_credentials:
                assert isinstance(repo_credential, RepoCredential)
                if not repo_credential.url and not repo_credential.user and not repo_credential.password:
                    continue
                auth_url = set_url_auth(git_url=repo_credential.url, user=repo_credential.user,
                                        password=repo_credential.password)
                self.commands.append(ShellArg('echo ' + auth_url + ' >> $HOME/.git-credentials'))
        return super(AuthenticateCheckoutStep, self).run()
