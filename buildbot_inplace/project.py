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


class RepoCredential(dict):
    @property
    def url(self):
        return self['url']

    @property
    def user(self):
        return self['user']

    @property
    def password(self):
        return self['password']

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
        if 'repoUser' not in self:
            return ''
        return self['repoUser']

    @property
    def repo_branch(self):
        if 'repoBranch' not in self:
            return ''
        return self['repoBranch']

    @property
    def repo_password(self):
        if 'repoPassword' not in self:
            return ''
        return self['repoPassword']

    @property
    def repo_mode(self):
        if 'repoMode' not in self:
            return 'incremental'

	if self['repoMode'] not in ['incremental', 'full']:
		raise Exception("Invalid repoMode in project configuration")
        return self['repoMode']

    @property
    def repo_credentials(self):
        if 'repoCredentials' not in self:
            return []
        repo_credentials = self['repoCredentials']
        return [RepoCredential(**credential_dict) for credential_dict in repo_credentials]

    @property
    def redmine_url(self):
        return self['redmineUrl']

    @property
    def redmine_username(self):
        return self['redmineUser']

    @property
    def redmine_password(self):
        return self['redminePassword']

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
