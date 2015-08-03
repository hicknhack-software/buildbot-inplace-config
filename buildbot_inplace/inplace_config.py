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
from yaml import safe_load


class Profile(dict):
    @property
    def name(self):
        return self['name']

    @property
    def platform(self):
        return self['platform']

    @property
    def command_key(self):
        return self['commands']

    @property
    def setups(self):
        return self['setup']


class Action(dict):
    @property
    def name(self):
        return self['name']

    @property
    def command_keys(self):
        return filter(lambda key: key != 'name', self.keys())

    def commands_for_key(self, command_key):
        return self.get(command_key)


class ProfileCommand:
    def __init__(self, name, commands):
        self.name = name
        self.commands = commands


class InplaceConfig:
    def __init__(self, profiles, actions):
        self.profiles = map(lambda profile_dict: Profile(**profile_dict), profiles)
        self.actions = map(lambda action_dict: Action(**action_dict), actions)

    @property
    def platform_names(self):
        return map(lambda profile: profile.platform, self.profiles)

    def profile_commands(self, profile):
        return filter(lambda action: action.commands,
                      map(lambda action: ProfileCommand(action.name, action.commands_for_key(profile.command_key)),
                          self.actions))

    @staticmethod
    def from_text(yaml_text):
        inplace_dict = safe_load(yaml_text)
        if not isinstance(inplace_dict, dict):
            return
        return InplaceConfig(**inplace_dict)
