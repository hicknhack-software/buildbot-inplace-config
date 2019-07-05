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


class User(dict):

    @staticmethod
    def users_key():
        return 'users'

    @property
    def name(self):
        if 'name' not in self:
            raise Exception("User requires at least a username")
        return self['name']

    @property
    def password(self):
        if 'password' not in self:
            return ''
        return self['password']

    @property
    def capabilities(self):
        if 'capabilities' not in self:
            return []
        return self['capabilities']

    @staticmethod
    def load(users_dir, users):
        files = glob(path.join(users_dir, '*.yml'))

        users.clear()
        for f in files:
            s = open(f, 'r')
            users_dict = safe_load(s)
            s.close()
            if not isinstance(users_dict, dict):
                continue

            if User.users_key() not in users_dict:
                raise Exception("No users configured")

            for user_dict in users_dict[User.users_key()]:
                if not isinstance(users_dict, dict):
                    continue
                user = User(**user_dict)
                users.named_set(user)
