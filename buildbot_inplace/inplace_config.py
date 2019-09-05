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

class RedmineDeployConfig(dict):
    @property
    def project(self):
        return self['project']

    @property
    def version(self):
        if 'version' in self:
            return self['version']

    @property
    def append_buildnumber(self):
        if 'append_buildnumber' in self:
            return self['append_buildnumber']
        return False

class Action(dict):
    @property
    def name(self):
        return self['name']

    @property
    def command_keys(self):
        return [key for key in self.keys() if key != 'name']

    def commands_for_key(self, key):
        commands = self.get(key)
        if isinstance(commands, dict) and 'commands' in commands:
            return flatten([commands.get('commands')])
        return flatten([commands])

    def products_for_key(self, key):
        commands_dict = self.get(key)
        if isinstance(commands_dict, dict) and 'products' in commands_dict:
            products = commands_dict.get('products')
            return flatten([products])
        return None

    def products_command_for_key(self, key):
        commands_dict = self.get(key)
        if isinstance(commands_dict, dict) and 'products_command' in commands_dict:
            return commands_dict.get('products_command')
        return None

    def redmine_deploy_for_key(self, key):
        commands_dict = self.get(key)
        if isinstance(commands_dict, dict) and 'redmine_deploy' in commands_dict:
            return RedmineDeployConfig(commands_dict.get('redmine_deploy'))
            
    def github_deploy_for_key(self, key):
        commands_dict = self.get(key)
        if isinstance(commands_dict, dict) and 'github_deploy' in commands_dict:
            return commands_dict.get('github_deploy')


class ProfileCommand:
    def __init__(self, name, commands, products=None, products_command=None, redmine_deploy=None, github_deploy=None):
        self.name = name
        self.commands = commands
        self.products = products
        self.products_command = products_command
        self.redmine_deploy = redmine_deploy
        self.github_deploy = github_deploy


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
        all_commands = [ProfileCommand(name=action.name,
                                       commands=action.commands_for_key(profile.command_key),
                                       products=action.products_for_key(profile.command_key),
                                       products_command=action.products_command_for_key(profile.command_key),
                                       redmine_deploy=action.redmine_deploy_for_key(profile.command_key),
                                       github_deploy=action.github_deploy_for_key(profile.command_key))
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
