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
from buildbot.config import BuilderConfig
from twisted.python import log
from buildbot.process.factory import BuildFactory
from buildbot.schedulers.forcesched import ForceScheduler
from buildbot.schedulers.triggerable import Triggerable
from inplace_build import InplaceBuildFactory
from project import Project
from setup_build import SetupBuildFactory
from slave import Slave


class NamedList(list):
    def named_set(self, elem):
        self.named_del(elem.name)
        self.append(elem)

    def named_del(self, name):
        for elem in self:
            if elem.name == name:
                self.remove(elem)

    def named_get(self, name):
        for elem in self:
            if elem.name == name:
                return elem

    def clear(self):
        del self[:]

    @property
    def names(self):
        return map(lambda elem: elem.name, self)


class Wrapper(dict):
    """ Wrapper for the configuration dictionary """

    def __init__(self, **kwargs):
        super(Wrapper, self).__init__(**kwargs)
        self._inplace_slaves = NamedList()
        self._projects = NamedList()

    @property
    def builders(self):
        return self.named_list('builders')

    @property
    def schedulers(self):
        return self.named_list('schedulers')

    @property
    def change_source(self):
        return self.named_list('change_source')

    @property
    def slaves(self):
        return self.named_list('slaves')

    @property
    def inplace_slaves(self):
        return self._inplace_slaves

    @property
    def projects(self):
        return self._projects

    def named_list(self, key):
        if key not in self:
            self[key] = NamedList()
        return self[key]

    def load_slaves(self, path):
        Slave.load(path, self.inplace_slaves, self.slaves)

    def load_projects(self, path):
        Project.load(path, self.projects)

    DUMMY_NAME = "Dummy"
    DUMMY_TRIGGER = "Trigger Dummy"

    def setup_inplace(self):
        self.builders.clear()
        self.schedulers.clear()
        builder_name = self.DUMMY_NAME
        trigger_name = self.DUMMY_TRIGGER
        slave_names = self.inplace_slaves.names
        self.builders.named_set(BuilderConfig(name=builder_name, slavenames=slave_names, factory=BuildFactory()))
        self.schedulers.named_set(ForceScheduler(name=trigger_name, builderNames=[builder_name]))
        for project in self.projects:
            builder_name = "%s_Builder" % project.name
            trigger_name = "Force_%s_Build" % project.name
            builder_factory = InplaceBuildFactory(self, project)
            self.builders.named_set(BuilderConfig(name=builder_name, slavenames=slave_names, factory=builder_factory))
            self.schedulers.named_set(ForceScheduler(name=trigger_name, builderNames=[builder_name]))

    def project_profile_slave_names(self, profile):
        return [slave.name
                for slave in self.inplace_slaves
                if set(profile.setups).issubset(set(slave.setups))
                and profile.platform in slave.platforms]

    def setup_project_inplace(self, project):
        self.setup_inplace()
        for profile in project.inplace.profiles:
            slave_names = self.project_profile_slave_names(profile)
            if not slave_names:
                log.msg("Failed to find slave for platform '%s' and setups '%s' (project '%s')" %
                        (profile.platform, ', '.join(profile.setups), project.name),
                        system='Inplace Config')
                continue  # profile not executable

            builder_name = "_".join([project.name, profile.platform, profile.name])
            trigger_name = _project_profile_trigger_name(project.name, profile)
            build_factory = SetupBuildFactory(self, project, profile)
            self.builders.named_set(BuilderConfig(name=builder_name, slavenames=slave_names, factory=build_factory))
            self.schedulers.named_set(Triggerable(name=trigger_name, builderNames=[builder_name]))

    def project_trigger_names(self, project):
        return [
            _project_profile_trigger_name(project.name, profile)
            for profile in project.inplace.profiles
            if self.project_profile_slave_names(profile)]

def _project_profile_trigger_name(project_name, profile):
    return "_".join([project_name, profile.platform, profile.name, "Trigger"])