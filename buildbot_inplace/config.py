""" Buildbot inplace config
(C) Copyright 2015-2019 HicknHack Software GmbH

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
import random

from buildbot.config import BuilderConfig
from buildbot.changes.filter import ChangeFilter
from buildbot.plugins import changes
from buildbot.plugins import schedulers
from buildbot.www.auth import UserPasswordAuth
from buildbot.www.authz.authz import Authz
from buildbot.www.authz.roles import RolesFromUsername
from buildbot.www.authz.endpointmatchers import AnyEndpointMatcher
from buildbot.www.authz.endpointmatchers import EnableSchedulerEndpointMatcher
from buildbot.www.authz.endpointmatchers import ForceBuildEndpointMatcher
from buildbot.www.authz.endpointmatchers import RebuildBuildEndpointMatcher
from buildbot.www.authz.endpointmatchers import StopBuildEndpointMatcher


from .project import Project
from .setup_build_factory import SetupBuildFactory
from .spawner_build_factory import SpawnerBuildFactory
from .user import User
from .worker import Worker


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
        return list(map(lambda elem: elem.name, self))


class Wrapper(dict):
    """ Wrapper for the configuration dictionary """

    def __init__(self, **kwargs):
        super(Wrapper, self).__init__(**kwargs)
        self._inplace_workers = NamedList()
        self._projects = NamedList()
        self._users = NamedList()
        self._roles = NamedList()

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
    def workers(self):
        return self.named_list('workers')

    @property
    def inplace_workers(self):
        return self._inplace_workers

    @property
    def projects(self):
        return self._projects

    @property
    def users(self):
        return self._users

    @property
    def roles(self):
        return self._roles

    def named_list(self, key):
        if key not in self:
            self[key] = NamedList()
        return self[key]

    def load_workers(self, path):
        Worker.load(path, self.inplace_workers, self.workers)

    def load_projects(self, path):
        Project.load(path, self.projects)

    def load_users(self, path):
        User.load(path, self.users)
        self.setup_users()

    def project_profile_worker_names(self, profile):
        return [worker.name
                for worker in self.inplace_workers
                if set(profile.setups).issubset(set(worker.setups))
                and profile.platform in worker.platforms]

    def setup_users(self):
        self['www']['auth'] = UserPasswordAuth(dict([(u.name, u.password) for u in self.users]))
        role_matcher = []
        allow_rules = []
        for user in self.users:
            role_matcher.append(RolesFromUsername(roles=user.capabilities, usernames=[user.name]))

        allow_rules.append(AnyEndpointMatcher(role='all', defaultDeny=False))
        allow_rules.append(ForceBuildEndpointMatcher(role='build'))
        allow_rules.append(ForceBuildEndpointMatcher(role='force_build'))

        allow_rules.append(StopBuildEndpointMatcher(role='build'))
        allow_rules.append(StopBuildEndpointMatcher(role='stop_build'))

        allow_rules.append(RebuildBuildEndpointMatcher(role='build'))
        allow_rules.append(RebuildBuildEndpointMatcher(role='rebuild'))

        allow_rules.append(EnableSchedulerEndpointMatcher(role='schedule'))

        # make sure to add a catch-all to disable anonymous access
        allow_rules.append(AnyEndpointMatcher(role='nobody'))
        self['www']['authz'] = Authz(allowRules=allow_rules, roleMatchers=role_matcher)

    def setup_git_poller(self, project):
        work_dir = './gitpoller-workdir/' + project.name
        self.change_source.append(changes.GitPoller(
            repourl=project.repo_url,
            branches=True,
            pollAtLaunch=True,
            project=project.name,
            workdir=work_dir,
            pollInterval=60,
        ))

        # Manually add and configure git credential store
        from subprocess import Popen
        from os.path import expanduser

        git_cred_path = expanduser("~/.git-credentials")
        Popen(["git", "init", "--bare", work_dir])
        try:
            cred_lines = set(open(git_cred_path).readlines())
        except IOError:
            cred_lines = set()

        # Prepare the GitPoller workdir with credentials
        for cred in project.repo_credentials:
            Popen(["git", "config", "--global", "credential.helper", "store"], cwd=work_dir)

            scheme, uri = cred.url.split("//")
            cred_lines.add(scheme + "//" + cred.user + ":" + cred.password + "@" + uri + '\n')

        open(git_cred_path, "w").writelines(cred_lines)

        # Register a scheduler that reacts to changes on the repository
        git_scheduler = schedulers.AnyBranchScheduler(
            name="Git-%s" % project.name,
            builderNames=[project.name],
            change_filter=ChangeFilter(project=project.name))

        self.schedulers.named_set(git_scheduler)

    def setup_inplace(self):
        self.builders.clear()
        self.schedulers.clear()
        worker_names = self.inplace_workers.names

        def pick_next_worker(_, worker_pool, build):
            if 'inplace_platform' not in build.properties:
                return
            platform = build.properties['inplace_platform']
            setups = set(build.properties['inplace_setups'])

            def is_option(worker):
                name = worker.name
                inplace_worker = self.inplace_workers.named_get(name)
                return setups.issubset(set(inplace_worker.setups)) and platform in inplace_worker.platforms

            possible_workers = [w for w in worker_pool if is_option(w.worker)]
            return random.choice(possible_workers) if possible_workers else None

        for project in self.projects:
            builder_name = "Inplace %s" % project.name
            trigger_name = "Build %s" % project.name
            spawner_name = project.name
            force_trigger_name = "Force-%s" % project.name

            builder_factory = SpawnerBuildFactory(self, trigger_name, project)
            builder_config = BuilderConfig(name=spawner_name, workernames=worker_names, factory=builder_factory)
            self.builders.named_set(builder_config)
            self.schedulers.named_set(schedulers.ForceScheduler(name=force_trigger_name, builderNames=[spawner_name]))

            inplace_builder_config = BuilderConfig(
                name=builder_name,
                workernames=worker_names,
                factory=SetupBuildFactory(self, project),
                nextWorker=pick_next_worker)
            inplace_scheduler = schedulers.Triggerable(
                name=trigger_name,
                builderNames=[builder_name])

            self.builders.named_set(inplace_builder_config)
            self.schedulers.named_set(inplace_scheduler)

        # Allow triggering through HTTP API at /change_hook
        self['www']['change_hook_dialects'] = {'base': True}

        # Also poll the repository (e.g. in case buildhost was shut down)
        for project in self.projects:
            if project.repo_type == 'git':
                self.setup_git_poller(project)
            else:
                raise Exception('SVN Repository Polling not implemented!')

            #nightly_scheduler = schedulers.Nightly(
            #    name="Nightly-%s" % project.name,
            #    builderNames=[project.name],
            #    hour=0
            #)
            #self.schedulers.named_set(nightly_scheduler)
