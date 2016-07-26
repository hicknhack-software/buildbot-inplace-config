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
from buildbot.steps.shell import ShellCommand
from buildbot.steps.shellsequence import ShellSequence
from steps.checkout import create_checkout_step
from steps.setup import SetupStep


class SetupBuildFactory(BuildFactory):
    """A Factory that creates environment-aware build steps from a configuration."""

    def __init__(self, config, project, profile):
        BuildFactory.__init__(self, [])
        env = {}

        for setup in profile.setups:
            desc = "Preparing %s" % setup
            prepare_dict = dict(name=desc, description=desc, descriptionDone=desc)
            self.addStep(SetupStep(setup, config=config, env=env, **prepare_dict))
        self.addStep(create_checkout_step(project))
        profile_commands = project.inplace.profile_commands(profile)
        for pc in profile_commands:
            shell_dict = dict(name=pc.name, description=pc.name, descriptionDone=pc.name)
            if len(pc.commands) == 1:
                self.addStep(ShellCommand(command=pc.commands[0], env=env, **shell_dict))
            else:
                self.addStep(ShellSequence(pc.commands, env=env, **shell_dict))
