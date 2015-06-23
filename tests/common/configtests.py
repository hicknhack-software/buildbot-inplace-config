''' Buildbot inplace config
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
'''

import unittest

from common.config import *

ProjectConfYaml = \
'''\
profiles:
- name: Profile1
	platform: Platform1
	commands: custom1
	setup:
	- Setup1

- name: Profile2
	platform: Platform2
	commands: custom2
	setup:
	- Setup2
	- Setup4

actions:
- name: Action1
	custom1:
		- 'Command1'
- name: Action2
	custom2:
		- 'Command2'
		- 'Command3'
	custom1:
		- 'Command1'
		- 'Command2'\
'''

completeProfileString = '''\
- name: ProfileName
	platform: PlatformName
	commands: custom
	setup: ['Setup']\
'''

noNameProfileString = '''\
- platform: PlatformName
	commands: custom
	setup: ['Setup']\
'''

noPlatformProfileString = '''\
- name: ProfileName
	commands: custom
	setup: ['Setup']\
'''

noCommandsProfileString = '''\
- name: ProfileName
	platform: PlatformName
	setup: ['Setup']\
'''

actionString = \
'''\
- name: Action
	custom:
		- 'Command'\
'''

class ProjectConfigurationParserTest(unittest.TestCase):

	def test_init(self):
		conf = ProjectConfiguration("Test", "TestGit", "git")

		self.assertNotEqual(conf.platforms, None)
		self.assertNotEqual(conf.profiles, None)
		self.assertNotEqual(conf.commandKeys, None)

	def test_parse(self):
		conf = ProjectConfigurationParser.fromYamlString(ProjectConfYaml)

		self.assertEqual(len(conf.platforms), 2)
		self.assertEqual(len(conf.profiles), 2)

		self.assertEqual(len(conf.commandKeys), 2)
		self.assertEqual(conf.commandKeys, set(["custom1", "custom2"]))

	def test_profile_parse(self):

		y = yaml.safe_load(completeProfileString)
		profile = ProjectConfigurationParser.profileFromYamlString(y[0])

		self.assertEqual(len(y), 1)
		self.assertEqual(profile.platform.name, "PlatformName")
		self.assertEqual(profile.setup, ["Setup"])

	def test_profile_no_platform(self):

		y = yaml.safe_load(noPlatformProfileString)

		with self.assertRaises(KeyError):
			profile = ProjectConfigurationParser.profileFromYamlString(y[0])

	def test_profile_no_commands(self):

		y = yaml.safe_load(noCommandsProfileString)

		with self.assertRaises(KeyError):
			profile = ProjectConfigurationParser.profileFromYamlString(y[0])

	def test_profile_no_name(self):

		y = yaml.safe_load(noNameProfileString)

		with self.assertRaises(KeyError):
			profile = ProjectConfigurationParser.profileFromYamlString(y[0])

	def test_action_parse(self):

		y = yaml.safe_load(actionString)
		action = ProjectConfigurationParser.actionFromYamlString(y[0], "custom")

		self.assertEqual(len(y), 1)
		self.assertEqual(len(action.commands), 1)
		self.assertEqual(action.name, "Action")
		self.assertEqual(action.commands, ["Command"])

class SlaveInformationTest(unittest.TestCase):

	SlaveDict = {"name": "Slave", "password": "Password", "shell": "bash", "setupDir": "/opt/setups", "platform": "Unix", "setups": ["gcc490"]}

	def test_init(self):
		d = SlaveInformationTest.SlaveDict
		slave = SlaveInformation(**d)

		self.assertEqual(slave.name, d["name"])
		self.assertEqual(slave.password, d["password"])
		self.assertEqual(slave.shell, d["shell"])
		self.assertEqual(slave.setupDir, d["setupDir"] + "/")
		self.assertEqual(slave.platform, d["platform"])
		self.assertEqual(slave.setups, d["setups"])

	def test_slave_info(self):

		class DummySlave:
			def __init__(self, name):
				self.name = name

		d = SlaveInformationTest.SlaveDict
		slaveInfo = SlaveInformation(**d)

		dummySlaveConfig = DummySlave(d["name"])
		bbConfig = BuildbotConfigurationWrapper()

		bbConfig.addSlave(dummySlaveConfig)
		bbConfig.registerSlaveInformation(slaveInfo)

		self.assertEqual(bbConfig.getSlaveByInfo(slaveInfo), dummySlaveConfig)
		self.assertEqual(bbConfig.retrieveSlaveInformation(slaveInfo.name), slaveInfo)
		self.assertEqual(bbConfig.availablePlatforms(), set(["Unix"]))


