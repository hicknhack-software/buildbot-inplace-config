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


class Role(dict):
    @property
    def name(self):
        return self['name']

    @property
    def capabilities(self):
        return self['capabilities']

    @staticmethod
    def roles_key():
        return 'roles'

    @staticmethod
    def load(users_dir, roles):
        files = glob(path.join(users_dir, '*.yml'))

        roles.clear();
        for f in files:
            s = open(f, 'r')
            roles_dict = safe_load(s)

            s.close()
            if not isinstance(roles_dict, dict):
                continue

            if Role.roles_key() not in roles_dict:
                raise Exception("No roles configured")

            for role_dict in roles_dict[Role.roles_key()]:
                role = Role(**role_dict)
                roles.named_set(role)