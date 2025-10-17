""" Buildbot inplace config
(C) Copyright 2015-2025 HicknHack Software GmbH

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

import stat
from twisted.internet import defer

from buildbot.process.results import SUCCESS, worst_status
from buildbot.steps.shell import ShellCommand
from . import configured_step_mixin
from . import checkout
from ..project import RepoCredential
from ..utilities import command_utilities
from .success import ShowStepIfSuccessful

class AuthenticateCheckoutStep(ShellCommand, configured_step_mixin.ConfiguredStepMixin):
    name = "Setup Git Authentication"
    haltOnFailure = True
    flunkOnFailure = True

    """A Step to store authentication on source checkouts."""
    def __init__(self, project=None, config=None, **kwargs):
        self.project = project
        self.global_config = config
        super().__init__(hideStepIf = ShowStepIfSuccessful, **kwargs)

    @defer.inlineCallbacks
    def run(self):
        repo_credentials = self.project.repo_credentials
        worker = self.global_config.inplace_workers.named_get(self.getWorkerName())
        worker_commands = command_utilities.get_worker_commands(worker_info=worker)
        if not repo_credentials:
            return SUCCESS

        content =  []
        for repo_credential in repo_credentials:
            assert isinstance(repo_credential, RepoCredential)
            if not repo_credential.url and not repo_credential.user and not repo_credential.password:
                continue

            auth_url = checkout.set_url_auth(repo_url=repo_credential.url, user=repo_credential.user,
                                                password=repo_credential.password)
            content.append(auth_url)

        credential_file = worker_commands.create_path_to([worker.utilities_dir, 'tmp.git-credentials'])
        yield self.downloadFileContentToWorker(credential_file, "\n".join(content), mode=stat.S_IRUSR | stat.S_IWUSR)

        self.command = ['git', 'config', '--global', 'credential.helper', 'store --file=%s' % credential_file]
        result = yield super().run()
        return result

class ClearCheckoutAuthenticationStep(ShellCommand, configured_step_mixin.ConfiguredStepMixin):
    name = "Clear Git Authentication"
    haltOnFailure = False
    flunkOnFailure = False
    command = ['git', 'config', '--global', '--remove-section', 'credential']

    """A Step to clean up any temporary authentication information for source checkouts."""
    def __init__(self, project=None, config=None, **kwargs):
        self.project = project
        self.global_config = config
        super().__init__(hideStepIf = ShowStepIfSuccessful, **kwargs)

    @defer.inlineCallbacks
    def run(self):
        worker = self.global_config.inplace_workers.named_get(self.getWorkerName())
        worker_commands = command_utilities.get_worker_commands(worker_info=worker)
        if not self.project.repo_credentials:
            return SUCCESS

        credential_file = worker_commands.create_path_to([worker.utilities_dir, 'tmp.git-credentials'])
        result = yield self.runRmFile(credential_file, abandonOnFailure=False)
        other_result = yield super().run()
        return worst_status(result, other_result)
