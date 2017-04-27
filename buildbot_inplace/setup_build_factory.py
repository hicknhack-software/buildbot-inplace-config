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
from .steps.setup_build_steps import SetupBuildSteps
from .steps.authenticate_checkout import AuthenticateCheckoutStep
from .steps.checkout import create_checkout_step


class SetupBuildFactory(BuildFactory):
    """A Factory that creates environment-aware build steps from a configuration."""

    def __init__(self, config, project):
        BuildFactory.__init__(self, steps=[])
        self.addStep(AuthenticateCheckoutStep(project))
        self.addStep(create_checkout_step(project))
        self.addStep(SetupBuildSteps(config))
