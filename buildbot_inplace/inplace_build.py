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
from buildbot.process.factory import BuildFactory

from buildbot.steps.trigger import Trigger
from steps.checkout import create_checkout_step
from steps.reconfig_buildmaster import ReconfigBuildmasterStep
from steps.retrieve_inplace import RetrieveInplaceConfigStep


def trigger_name(project_name, platform_name):
    return "%(project_name)s_%(platform_name)s_Trigger" % locals()


class InplaceTriggerBuilds(Trigger):
    def __init__(self, config, project, **kwargs):
        super(InplaceTriggerBuilds, self).__init__(schedulerNames=["dummy"], **kwargs)
        self.config = config
        self.project = project

    # @defer.inlineCallbacks
    def run(self):
        self.schedulerNames = self.config.project_trigger_names(self.project)
        return super(InplaceTriggerBuilds, self).run()


class InplaceBuildFactory(BuildFactory):
    """ A factory that provides Steps to checkout a repository, reads its configuration
        Finally it creates and triggers the builds accordingly."""

    REGISTER_DESC = 'Registering Builds'
    REGISTER_DICT = dict(name=REGISTER_DESC, description=REGISTER_DESC, descriptionDone=REGISTER_DESC)
    RESET_DESC = 'Resetting Configuration'
    RESET_DICT = dict(name=RESET_DESC, description=RESET_DESC, descriptionDone=RESET_DESC)
    TRIGGER_DESC = 'Triggering Builds'
    TRIGGER_DICT = dict(name=TRIGGER_DESC, description=TRIGGER_DESC, descriptionDone=TRIGGER_DESC)

    def __init__(self, config, project):
        super(InplaceBuildFactory, self).__init__()
        self.addStep(create_checkout_step(project))
        self.addStep(RetrieveInplaceConfigStep(project, haltOnFailure=True))
        self.addStep(ReconfigBuildmasterStep(config, project,
                                             update_from_project=True,
                                             haltOnFailure=True,
                                             **self.REGISTER_DICT))
        self.addStep(InplaceTriggerBuilds(config, project,
                                          updateSourceStamp=True,
                                          waitForFinish=True,
                                          **self.TRIGGER_DICT))
        self.addStep(ReconfigBuildmasterStep(config, project,
                                             update_from_project=False,
                                             **self.RESET_DICT))
