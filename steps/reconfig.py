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

from buildbot import config
from buildbot.process import buildstep, logobserver
from buildbot.steps import master, shell, shellsequence
from twisted.internet import defer
from buildbot.schedulers import triggerable

from base import EnvironmentParser, ShowStepIfSuccessful, triggerableName
from ..common.config import ProjectConfigurationParser
	
'''A Step that executes a command in a given environment.'''
class EnvironmentAwareStep(buildstep.ShellMixin, buildstep.BuildStep):

	def __init__(self, envDict, cmd, **kwargs):

		self.envDict = envDict
		self.command = cmd

		kwargs['env'] = envDict
		kwargs = self.setupShellMixin(kwargs, prohibitArgs=['command'])
		buildstep.BuildStep.__init__(self, **kwargs)	

	@defer.inlineCallbacks
	def run(self):
		cmd = yield self.makeRemoteShellCommand(command=self.command, stdioLogName="stdio")
		yield self.runCommand(cmd)

		yield defer.returnValue(cmd.results())

'''A Step that executes multiple commands in a given environment.'''
class EnvironmentAwareShellSequence(shellsequence.ShellSequence):

	def __init__(self, envDict, cmds, **kwargs):

		self.envDict = envDict
		self.commands = cmds

		kwargs['env'] = envDict
		kwargs['commands'] = [shellsequence.ShellArg(command=x, logfile="stdio") for x in cmds]

		shellsequence.ShellSequence.__init__(self, **kwargs)

'''A Step that retrieves the environment after a command.'''
class RetrieveEnvironmentStep(buildstep.ShellMixin, buildstep.BuildStep):

	Delimiters = {
		"cmd": ";",
		"bash": ":"
	}

	def __init__(self, bbConfig, envDict, setup, **kwargs):

		commands = []

		self.bbConfig = bbConfig
		self.envDict = envDict
		self.setup = setup

		kwargs = self.setupShellMixin(kwargs, prohibitArgs=['command'])
		buildstep.BuildStep.__init__(self, **kwargs)

	@defer.inlineCallbacks
	def run(self):

		cmd = yield self.makeRemoteShellCommand(
				command=[
					self._addCreateShell(), 
					self._createSubcommand()
				], 
				stdioLogName="envLog"
			)

		self._addRetrieveEnvironment()

		yield self.runCommand(cmd)
		yield defer.returnValue(cmd.results())

	#logobserver
	def _addRetrieveEnvironment(self):
		slaveInfo = self.bbConfig.retrieveSlaveInformation(self.getSlaveName())

		self.consumer = EnvironmentParser(self.envDict, RetrieveEnvironmentStep.Delimiters[slaveInfo.shell])		
		self.addLogObserver('envLog', logobserver.LineConsumerLogObserver(self.consumer._retrieveEnvironment))

	#creates a command that start a new shell
	def _addCreateShell(self):
		slaveInfo = self.bbConfig.retrieveSlaveInformation(self.getSlaveName())

		if slaveInfo.shell == "bash":
			return [slaveInfo.shell, '-c']
		else:
			return [slaveInfo.shell, '/c']

	#creates commands to make sure the setup script is executable and to source the environment
	def _createSubcommand(self):
		slaveInfo = self.bbConfig.retrieveSlaveInformation(self.getSlaveName())

		subCommand = []

		setupScript = self._getSetupScript()

		if self.setup and slaveInfo.shell == 'bash': 
			subCommand.append('chmod +x %s;' % setupScript)
		subCommand.append('. %s;' % setupScript) 

		subCommand.append('env')

		return "".join(subCommand)

	#helpers
	def _getSetupScript(self):
		slaveInfo = self.bbConfig.retrieveSlaveInformation(self.getSlaveName())
		suffix = ".sh"

		if "Windows" in slaveInfo.platform:
			suffix = ".bat"

		return "".join([slaveInfo.setupDir, self.setup, suffix])

'''A Step that parses a project configuration (.buildbot.yml).'''
class RetrieveProjectConfigurationStep(buildstep.ShellMixin, buildstep.BuildStep):

	def __init__(self, projectConfig, **kwargs):

		self.projectConfig = projectConfig
		kwargs = self.setupShellMixin(kwargs, prohibitArgs=['command'])
		buildstep.BuildStep.__init__(self, name="Update Configuration", hideStepIf=ShowStepIfSuccessful, **kwargs)
    
	@defer.inlineCallbacks
	def run(self):
		self._sync_addlog_deferreds = []
		self.configLog = []

		cmd = yield self.makeRemoteShellCommand(command=["cat", ".buildbot.yml"], stdioLogName="config")
		self.addLogObserver('config', logobserver.LineConsumerLogObserver(self._consumeLog))

		yield self.runCommand(cmd)
		if cmd.didFail():
			buildstep.BuildStepFailed()

		ProjectConfigurationParser.parseYamlString("".join(self.configLog), self.projectConfig)

		yield defer.returnValue(cmd.results())

	def _consumeLog(self):
	    while True:
	        stream, line = yield
	        if stream == 'o':
	            self.configLog.append(line + "\n")

class ProfileNotFulfilledException(Exception):
	pass

''' A Step that reconfigures the Buildmaster.'''
class ReconfigBuildmasterStep(master.MasterShellCommand):

	def __init__(self, bbConfig, projectConfig, updateFromProject, **kwargs):
		self.kwargs = kwargs
		self.bbConfig = bbConfig
		self.projectConfig = projectConfig
		self.projectName = projectConfig.projectName
		self.updateFromProject = updateFromProject

		master.MasterShellCommand.__init__(self, command=["echo", "Reconfigured Master"], hideStepIf=ShowStepIfSuccessful, **kwargs)

	def start(self):
		try:
			self._addBuilders()
		except ProfileNotFulfilledException as e:
			from buildbot.status.results import FAILURE
			self.addCompleteLog("errorlog", "Failing: %s" % str(e))
			return FAILURE

		if self.updateFromProject:
			newConfig  = self._createMasterConfig()
			self.master.reconfigServiceWithBuildbotConfig(newConfig)
		else:
			self.master.reconfig()

		return master.MasterShellCommand.start(self)

	def _createMasterConfig(self):
		configDict = self.bbConfig.getConfigDict()
		try:
			masterConfig = config.MasterConfig()
			filename = None
			masterConfig.load_global(filename, configDict)
			masterConfig.load_validation(filename, configDict)
			masterConfig.load_db(filename, configDict)
			masterConfig.load_mq(filename, configDict)
			masterConfig.load_metrics(filename, configDict)
			masterConfig.load_caches(filename, configDict)
			masterConfig.load_schedulers(filename, configDict)
			masterConfig.load_builders(filename, configDict)
			masterConfig.load_slaves(filename, configDict)
			masterConfig.load_change_sources(filename, configDict)
			masterConfig.load_status(filename, configDict)
			masterConfig.load_user_managers(filename, configDict)
			masterConfig.load_www(filename, configDict)
			masterConfig.load_services(filename, configDict)

			# run some sanity checks
			masterConfig.check_single_master()
			masterConfig.check_schedulers()
			masterConfig.check_locks()
			masterConfig.check_builders()
			masterConfig.check_status()
			masterConfig.check_horizons()
			masterConfig.check_ports()

		except Exception as e:
			raise Exception("Could not reconfigure Buildbot: " + str(e))

		return masterConfig

	def _getSlavesNamesForProfile(self, profile):

		def setupSatisfied(requested, existing):
			return set(requested).issubset(set(existing))			

		platformName = profile.platform.name
		slaveInfos = filter( lambda s : s.platform == platformName and setupSatisfied(profile.setup, s.setups), self.bbConfig.slaveInfo )

		return map(lambda s : s.name, slaveInfos)

	def _addBuilders(self):
		from ..factories.reconfig import EnvironmentAwareBuildFactory # avoid cyclic import

		builderNamesByPlatform = {}

		for profile in self.projectConfig.profiles:
			applicableSlaves = self._getSlavesNamesForProfile(profile)
			if not applicableSlaves:
				continue

			#update associations between platform and builders
			platformName = profile.platform.name
			
			if platformName not in builderNamesByPlatform:
				builderNamesByPlatform[platformName] = []

			builderName = "_".join([self.projectName, platformName, profile.name])
			builderNamesByPlatform[platformName].append(builderName)

			# create builder
			self.bbConfig.addBuilder(
				config.BuilderConfig(
					name=builderName, 
					slavenames=applicableSlaves,
					factory=EnvironmentAwareBuildFactory(self.bbConfig, self.projectConfig, profile)
				)
			)

		if not builderNamesByPlatform:
			raise ProfileNotFulfilledException("No slaves fulfil the profiles of this project!")

		for platform in self.bbConfig.availablePlatforms():
			if platform not in builderNamesByPlatform:
				builderNamesByPlatform[platform] = ["DummyBuilder"]

		for platform in self.bbConfig.availablePlatforms():
			if platform in builderNamesByPlatform:
				self._addTriggerable(platform, builderNamesByPlatform[platform])


	def _addTriggerable(self, platformName, builderNames):
		name = triggerableName(self.projectName, platformName)
		self.bbConfig.addScheduler(triggerable.Triggerable(name = name, builderNames=builderNames))		