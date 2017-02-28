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
from buildbot.process.factory import BuildFactory
from buildbot.process.properties import Properties
from twisted.internet import defer
from buildbot.steps.trigger import Trigger

from .steps.configured_step_mixin import ConfiguredStepMixin
from .steps.checkout import create_checkout_step


def trigger_name(project_name, platform_name):
    return "%(project_name)s_%(platform_name)s_Trigger" % locals()


class InplaceTriggerBuilds(Trigger, ConfiguredStepMixin):
    def __init__(self, config, project, scheduler, **kwargs):
        self.global_config = config
        self.project = project
        self.build_config = None
        super(InplaceTriggerBuilds, self).__init__(schedulerNames=[scheduler], **kwargs)

    @defer.inlineCallbacks
    def run(self):
        self.build_config = yield self.getInplaceConfig()
        rv = yield super(InplaceTriggerBuilds, self).run()
        defer.returnValue(rv)

    def createTriggerProperties(self, props):
        # do not mark properties from trigger
        return props

    @defer.inlineCallbacks
    def getSchedulersAndProperties(self):
        sched_name = self.schedulerNames[0]
        triggered_schedulers = []
        log = None

        for profile in self.build_config.profiles:
            if not self.global_config.project_profile_worker_names(profile):
                if not log:
                    log = yield self.addLog_newStyle("skipped builds", "t")
                yield log.addContent("Could not find worker for: {0} on platform {1}\n".format(profile.setups, profile.platform))
                continue

            props_to_set = Properties()
            props_to_set.update(self.set_properties, "Trigger")
            props_to_set.setProperty('inplace_project', self.project.name, "Master")
            props_to_set.setProperty('inplace_profile', profile.name, ".buildbot.yml")
            props_to_set.setProperty('inplace_platform', profile.platform, ".buildbot.yml")
            props_to_set.setProperty('inplace_setups', profile.setups, ".buildbot.yml")

            triggered_schedulers.append((sched_name, props_to_set))

        if log:
            yield log.finish()

        defer.returnValue(triggered_schedulers)


class SpawnerBuildFactory(BuildFactory):
    """ A factory that provides Steps to checkout a repository, reads its configuration
        Finally it creates and triggers the builds accordingly."""

    TRIGGER_DESC = 'Triggering Builds'
    TRIGGER_DICT = dict(name=TRIGGER_DESC, description=TRIGGER_DESC, descriptionDone=TRIGGER_DESC)

    def __init__(self, config, scheduler, project):
        super(SpawnerBuildFactory, self).__init__()
        self.addStep(create_checkout_step(project))
        self.addStep(InplaceTriggerBuilds(config, project, scheduler,
                                          updateSourceStamp=True,
                                          waitForFinish=True,
                                          **self.TRIGGER_DICT))
