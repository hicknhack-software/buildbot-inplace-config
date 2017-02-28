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
from glob import glob
from os import path
from yaml import safe_load


class Project(dict):
    @property
    def name(self):
        return self['name']

    @property
    def repo_type(self):
        return self['repoType']

    @property
    def repo_url(self):
        return self['repoUrl']

    @property
    def repo_user(self):
        return self['repoUser']

    @property
    def repo_password(self):
        return self['repoPassword']

    @property
    def inplace(self):
        return self.get('inplace')

    @inplace.setter
    def inplace(self, value):
        self['inplace'] = value

    @staticmethod
    def load(projects_path, projects):
        files = glob(path.join(projects_path, "*.yml"))
        if not files:
            raise Exception("No projects found in %s!" % projects_path)

        projects.clear()
        for project_file in files:
            s = open(project_file, 'r')
            project_dict = safe_load(s)
            s.close()
            if not isinstance(project_dict, dict):
                continue
            project = Project(**project_dict)
            projects.named_set(project)
