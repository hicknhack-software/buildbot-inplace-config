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
from buildbot.process.buildstep import BuildStepFailed
from buildbot.steps.worker import CompositeStepMixin
from twisted.internet import defer

from buildbot_inplace.inplace_config import InplaceConfig, BuildbotYmlInvalid


class ConfiguredStepMixin(CompositeStepMixin):
    def __init__(self):
        pass

    def getResultSummary(self):
        if self.descriptionDone is not None:
            return {u'step': self.descriptionDone}
        else:
            super(ConfiguredStepMixin, self).getResultSummary()


    @defer.inlineCallbacks
    def get_inplace_config(self):
        try:
            inplace_text = yield self.getFileContentFromWorker('.buildbot.yml', abandonOnFailure=True)
        except BuildStepFailed as e:
            self.descriptionDone = 'unable to fetch .buildbot.yml'
            self.addCompleteLog(
                "error",
                "Please put a file named .buildbot.yml at the root of your repository:\n{0}".format(e))
            #self.addHelpLog()
            raise
        self.addCompleteLog('.buildbot.yml', inplace_text)

        try:
            config = InplaceConfig.from_text(inplace_text)
        except BuildbotYmlInvalid as e:
            self.descriptionDone = 'bad .buildbot.yml'
            self.addCompleteLog(
                "error",
                ".buildbot.yml is invalid:\n{0}".format(e))
            #self.addHelpLog()
            raise
        defer.returnValue(config)
