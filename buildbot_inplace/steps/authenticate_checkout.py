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
from ..utilities.command_utilities import get_worker_commands


class AuthenticateCheckoutStep(ShellSequence, ConfiguredStepMixin):
    def __init__(self, project=None, config=None, **kwargs):
        self.project = project
        self.global_config = config
        self.descriptionDone = u'Authentication finished!'
        super(AuthenticateCheckoutStep, self).__init__(commands=[], **kwargs)

    def run(self):
        repo_credentials = self.project.repo_credentials
        worker = self.global_config.inplace_workers.named_get(self.getWorkerName())
        worker_commands = get_worker_commands(worker_info=worker)
        if not repo_credentials:
            self.commands.append(ShellArg(command=worker_commands.echo_command))

        else:
            credential_file = worker_commands.create_path_to([worker_commands.home_path_var, '.git-credentials'])
            remove_command = ' '.join([worker_commands.remove_command, credential_file])
            self.commands.extend([ShellArg(remove_command),
                                  ShellArg('git config --global credential.helper store')])

            for repo_credential in repo_credentials:
                assert isinstance(repo_credential, RepoCredential)
                if not repo_credential.url and not repo_credential.user and not repo_credential.password:
                    continue
                auth_url = set_url_auth(git_url=repo_credential.url, user=repo_credential.user,
                                        password=repo_credential.password)
                echo_credentials_command = ' '.join([worker_commands.echo_command,
                                                     auth_url,
                                                     worker_commands.append_output_to_file,
                                                     credential_file
                                                     ])
                self.commands.append(ShellArg(echo_credentials_command))
        return super(AuthenticateCheckoutStep, self).run()

    def start(self):
        raise NotImplementedError("Use run()")


class ClearCheckoutAuthenticationStep(ShellSequence):
    def __init__(self, config=None, **kwargs):
        self.global_config = config
        self.descriptionDone = u'Authentication data cleared!'
        super(ClearCheckoutAuthenticationStep, self).__init__(commands=[], **kwargs)

    def run(self):
        worker = self.global_config.inplace_workers.named_get(self.getWorkerName())
        worker_commands = get_worker_commands(worker_info=worker)

        # 'rm -f $HOME/.git-credentials'
        credential_file = worker_commands.create_path_to([worker_commands.home_path_var, '.git-credentials'])
        remove_command = ' '.join([worker_commands.remove_command, credential_file])

        self.commands.extend([ShellArg(remove_command),
                              ShellArg('git config --global --unset credential.helper')])
        return super(AuthenticateCheckoutStep, self).run()

    def start(self):
        raise NotImplementedError("Use run()")
