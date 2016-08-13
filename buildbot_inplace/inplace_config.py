""" Buildbot inplace config
(C) Copyright 2016 HicknHack Software GmbH

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
from buildbot.util import flatten


class BuildbotYmlInvalid(Exception):
    pass


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
        return flatten([self.get('setups', self.get('setup', []))])


class Action(dict):
    @property
    def name(self):
        return self['name']

    @property
    def command_keys(self):
        return [key for key in self.keys() if key != 'name']

    def commands_for_key(self, key):
        return flatten([self.get(key)])


class ProfileCommand:
    def __init__(self, name, commands):
        self.name = name
        self.commands = commands


class InplaceConfig:
    def __init__(self, profiles, actions):
        self.profiles = [Profile(**profile_dict) for profile_dict in profiles]
        self.actions = [Action(**action_dict) for action_dict in actions]

    @property
    def platform_names(self):
        return [profile.platform for profile in self.profiles]

    def profile_named_get(self, name):
        for profile in self.profiles:
            if profile.name == name:
                return profile
        return None

    def profile_commands(self, profile):
        all_commands = [ProfileCommand(action.name, action.commands_for_key(profile.command_key))
                        for action in self.actions]
        return [cmd for cmd in all_commands if cmd.commands]

    @staticmethod
    def from_text(yaml_text):
        try:
            inplace_dict = safe_load(yaml_text)
        except Exception as e:
            raise BuildbotYmlInvalid("Invalid YAML data\n" + str(e))
        if not isinstance(inplace_dict, dict):
            raise BuildbotYmlInvalid("YAML should contain a dict")
        return InplaceConfig(**inplace_dict)
