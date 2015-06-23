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
from common.base import NamedInstance, Platform, Profile, Action, Dependency

def createName(cls):
	return str(cls)

def createPlatform():
	platformDict = { "name": createName(Platform)}
	return Platform(**platformDict)

class NamedInstanceTest(unittest.TestCase):

	def test_init(self):
		d = { "name": createName(NamedInstance)}
		instance = NamedInstance(**d)

		self.assertEqual(instance.name, d["name"])

class PlatformTest(unittest.TestCase):

	def test_init(self):
		d = { "name": createName(Platform)}
		platform = Platform(**d)

		self.assertEqual(platform.name, d["name"])

class ProfileTest(unittest.TestCase):

	def test_init(self):

		dep = Dependency(createName(Dependency))
		platform = createPlatform()

		profileDict = { "name": createName(Profile), "setup": [dep], "platform": platform, "commands" : ["custom"] }
		profile = Profile(**profileDict)

		self.assertEqual(profile.name, profileDict["name"])
		self.assertEqual(profile.setup, profileDict["setup"])

		self.assertEqual(profile.platform, platform)

class DependencyTest(unittest.TestCase):

	def test_init(self):
		d1 = Dependency("1")
		d2 = Dependency(name="2")

		self.assertEqual(d1.name, "1")
		self.assertEqual(d2.name, "2")

class ActionTest(unittest.TestCase):

	def test_init(self):
		platform = createPlatform()
		commands = ["./configure", "make", "make test", "make install"]
		d = {"name": createName(Action), "commands":commands}

		a = Action(**d)

		self.assertEqual(a.name, d["name"])
		self.assertEqual(a.commands, commands)
