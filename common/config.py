''' Twofold-Qt
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

import operator
import yaml

from .base import Profile, Platform, Dependency, Action

''' Parses .yml project configuration'''
class ProjectConfigurationParser:

	@staticmethod
	def fromYamlString(string):
		conf = ProjectConfiguration("Test", "TestGit", "git")
		ProjectConfigurationParser.parseYamlString(string, conf)

		return conf

	@staticmethod
	def parseYamlFile(filename, target):
		try:
			yaml_string = open(filename).read()
			ProjectConfigurationParser.parseYamlString(yaml_string, target)
		except:
			raise Exception("Could not load configuration from " + filename)

	@staticmethod
	def parseYamlString(yaml_string, target):
		try:
			y = yaml.safe_load(yaml_string)
			target._parseProfiles(y)
			target._parseActions(y)
		except Exception as exc:
			raise Exception("Could not parse configuration: " + str(exc))

	@staticmethod
	def profileFromYamlString(obj):
		platformName = obj["platform"]
		platformDict = {"name": obj["platform"]}

		obj["platform"] = Platform(**platformDict)
		return Profile(**obj)

	@staticmethod
	def actionFromYamlString(obj, commandKey):
		try:
			commands = obj[commandKey]
			d = {
				'name': obj['name'],
				'commands': commands,
				'commandKey': commandKey
			}
			return Action(**d)
		except:
			pass

'''Model of a project configuration that resides in a repository as a .yml file.'''

class ProjectConfiguration:

	def __init__(self, name, repoUrl, repoType):
		self.projectName = name
		self.repoUrl = repoUrl
		self.repoType = repoType
		self.profiles = set()
		self.platforms = set()
		self.commandKeys = set()
		self.commandsByKey = {}

	def platform_dependencies(self, name):
		s = set()
		for profile in self.profiles:
			for x in profile.dependencies:
				if profile.platform is name:
					s.add(x) 
					
		return sorted(s, key=operator.attrgetter('name'))

	def commands(self, commandKey):
		return self.commandsByKey[commandKey]

	def _parseProfiles(self, config):
		self.profiles.clear()
		self.platforms.clear()
		self.commandKeys.clear()		
		
		if isinstance(config, dict):
			for profile in config["profiles"]:
				prof = ProjectConfigurationParser.profileFromYamlString(profile)
				self.profiles.add(prof)
				self.platforms.add(prof.platform)
				self.commandKeys.add(prof.commands)

	def _parseActions(self, config):
		self.commandsByKey.clear()

		if not isinstance(config, dict):
			return

		for action in config["actions"]:
			for commandKey in self.commandKeys:
				act = ProjectConfigurationParser.actionFromYamlString(action, commandKey)
				if act is not None:
					if commandKey not in self.commandsByKey:
						self.commandsByKey[commandKey] = []
					self.commandsByKey[commandKey].append(act)

class SlaveInformation:

	ShellSuffix = {
		"bash": ".sh",
		"cmd": ".bat"
	}

	def __init__(self, **kwargs):
		self.name = kwargs["name"]
		self.password = kwargs["password"]
		self.shell = kwargs["shell"]
		self.setupDir = kwargs["setupDir"]
		self.platform = kwargs["platform"]
		self.setups = kwargs["setups"]

		self.buildbotConfig = None

		self._ensureSetupDir()

	def getSlaveConfig(self):
		try:
			return self.buildBotConfig.getSlaveByInfo(self)
		except:
			pass

	def setBuildbotConfig(self, buildbotConfig):
		self.buildbotConfig = buildBotConfig

	def _ensureSetupDir(self):
		self.setupDir.replace("\\", "/")
		if self.setupDir[-1] is not "/":
			self.setupDir += "/"

class BuildbotConfigurationWrapper:

	def __init__(self):
		self.config = dict()
		self.config['db'] = {'db_url' : "sqlite:///state.sqlite"}
		self.config['status'] = []
		self.config['www'] = dict(port=8020, plugins=dict(waterfall_view={}, console_view={})) 
		self.slaveInfo = []

	''' These methods are called from master.cfg '''

	def addBuilder(self, builder):
		self._maybeRemoveNamedEntity('builders', builder.name)
		self._addToArray('builders', builder)

	def addChangeSource(self, changeSource):
		self._addToArray('change_source', changeSource)

	def addScheduler(self, scheduler):
		self._maybeRemoveNamedEntity('schedulers', scheduler.name)
		self._addToArray('schedulers', scheduler)

	def addSlave(self, slave):
		self._addToArray('slaves', slave)

	def getSlaveByInfo(self, slaveInfo):
		for s in self.config['slaves']:
			if s.name == slaveInfo.name:
				return s

	def retrieveSlaveInformation(self, slaveName):
		for s in self.slaveInfo:
			if s.name == slaveName:
				return s

	def registerSlaveInformation(self, slaveInfo):
		self.slaveInfo.append(slaveInfo)

	def availablePlatforms(self):
		platforms = set()
		for s in self.slaveInfo:
			platforms.add(s.platform)

		return platforms
	
	def setConnection(self, url, port):
		self.config['buildbotURL'] = url
		self.config['protocols'] = {'pb': {'port': port}}

	def setTitle(self, title):
		self.config['title'] = title

	def setTitleUrl(self, titleUrl):
		self.config['titleURL'] = titleUrl

	def getConfigDict(self):
		return self.config

	''' Privates '''

	def _addToArray(self, key, obj):
		self._ensureArray(key)
		self.config[key].append(obj)

	def _ensureArray(self, entry):
		if entry not in self.config:
			self.config[entry] = []

	def _maybeRemoveNamedEntity(self, key, name):
		if key not in self.config:
			return 

		for e in self.config[key]:
			if e.name == name:
				self.config[key].remove(e)


