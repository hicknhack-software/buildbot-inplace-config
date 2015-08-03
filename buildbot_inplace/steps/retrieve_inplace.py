""" Buildbot inplace config
(C) Copyright 2015 HicknHack Software GmbH

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
from twisted.internet import defer
from buildbot.process.buildstep import BuildStep, ShellMixin, BuildStepFailed
from buildbot.process.logobserver import LineConsumerLogObserver
from ..inplace_config import InplaceConfig
from .success import ShowStepIfSuccessful


class RetrieveInplaceConfigStep(ShellMixin, BuildStep):
    NAME = "Retrieve Inplace Config"
    COMMAND = ["cat", ".buildbot.yml"]
    LOG_NAME = "inplace"

    def __init__(self, project, **kwargs):
        self.inplace_lines = None
        self.project = project
        kwargs = self.setupShellMixin(kwargs, prohibitArgs=['command'])
        BuildStep.__init__(self,
                           name=self.NAME,
                           hideStepIf=ShowStepIfSuccessful, **kwargs)

    @defer.inlineCallbacks
    def run(self):
        self.inplace_lines = []
        cmd = yield self.makeRemoteShellCommand(command=self.COMMAND, stdioLogName=self.LOG_NAME)
        self.addLogObserver(self.LOG_NAME, LineConsumerLogObserver(self._consume_log))
        yield self.runCommand(cmd)
        if cmd.didFail():
            BuildStepFailed()
        inplace_config = InplaceConfig.from_text('\n'.join(self.inplace_lines))
        # inplace_config.check(self)
        self.project.inplace = inplace_config
        yield defer.returnValue(cmd.results())

    def _consume_log(self):
        while True:
            stream, line = yield
            if stream == 'o':
                self.inplace_lines.append(line)
