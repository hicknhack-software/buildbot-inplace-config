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

import re

from buildbot.process import factory
from buildbot.steps import trigger, shellsequence
from buildbot.steps.source import git

from ..common.config import *
from ..steps import reconfig
from ..steps.base import ShowStepIfSuccessful, triggerableName

reload(reconfig)

def infuseCredentials(gitUrl, user, password):
	m = re.search("(://)", gitUrl)
	idx = m.end()
	if idx >= 0:
		credString = "%s:%s@" % (user, password)
		return (gitUrl[:idx] + credString + gitUrl[idx:])

	raise Exception("Url Format not supported: %s" % gitUrl)

def addCheckoutStep(factory):
	repoUrl = factory.projectConfig.repoUrl
	repoType = factory.projectConfig.repoType
	repoUser = factory.projectConfig.repoUser
	repoPassword = factory.projectConfig.repoPassword

	description="Checkout"
	checkoutDict = { 'name': description, 'description': description, 'descriptionDone': description, 'hideStepIf': ShowStepIfSuccessful }

	if repoType == "git":
		modifiedRepoUrl = repoUrl
		if repoUser and repoPassword:
			modifiedRepoUrl = infuseCredentials(modifiedRepoUrl, repoUser, repoPassword)
		factory.addStep(git.Git(modifiedRepoUrl, mode='incremental', submodules=True, **checkoutDict))
	else:
		raise Exception("Repotype '" + str(repoType) + "' not supported.")

'''A Factory that create environment-aware build steps from a configuration.'''
class EnvironmentAwareBuildFactory(factory.BuildFactory):

	def __init__(self, bbConfig, projectConfig, profile):

		factory.BuildFactory.__init__(self, [])

		self.bbConfig = bbConfig
		self.projectConfig = projectConfig
		self.profile = profile

		self.dict = {}
		self._addEnvironmentInitSteps()
		addCheckoutStep(self)
		self._addConfiguredBuildSteps()

	def _addEnvironmentInitSteps(self):
		
		for setup in self.profile.setup:
			desc = "Preparing %s" % setup
			stepDict = {
				'description': desc,
				'name': desc,
				'descriptionDone': desc
			}

			self.addStep(reconfig.RetrieveEnvironmentStep(self.bbConfig, self.dict, setup, **stepDict))

	def _addConfiguredBuildSteps(self):
		actions = self.projectConfig.commands(self.profile.commands)
		for action in actions:
			actionDict = {
				'name': action.name,
				'description': action.name,
				'descriptionDone': action.name
			}

			assert action.commands, "No commands found for %s:%s" % (self.profile.name, action.name)
			if len(action.commands) == 1:
				self.addStep(reconfig.EnvironmentAwareStep(self.dict, action.commands[0], **actionDict))
			else:
				cmds = [c for c in action.commands]
				self.addStep(reconfig.EnvironmentAwareShellSequence(self.dict, cmds, **actionDict))			

''' A factory that provides Steps to checkout a repository, reads its configuration and create and trigger builds accordingly.'''
class BuildTriggerFactory(factory.BuildFactory):
	reconfigDesc = 'Registering Builds'
	resetDesc = 'Resetting Configuration'

	reconfigDict = {'name': reconfigDesc, 'description': reconfigDesc, 'descriptionDone': reconfigDesc}
	resetDict = {'name': resetDesc, 'description': resetDesc, 'descriptionDone': resetDesc}

	triggerDesc = 'Triggering Builds'
	triggerDict = {'name': triggerDesc, 'description': triggerDesc, 'descriptionDone': triggerDesc}

	def __init__(self, buildBotConfig, projectConfig):

		factory.BuildFactory.__init__(self, [])

		self.buildBotConfig = buildBotConfig
		self.projectConfig = projectConfig

		addCheckoutStep(self)
		self._addReconfigurationSteps(projectName)

	def _triggerableNames(self):
		names = []

		for platform in self.buildBotConfig.availablePlatforms():
			names.append(triggerableName(self.projectConfig.projectName, platform))

		return names

	def _addReconfigurationSteps(self, projectName):

		# Checkout - Parse Config - Reconfigure with new Config - Trigger Builds - Load old Config
		self.addStep(reconfig.RetrieveProjectConfigurationStep(self.projectConfig, haltOnFailure=True))
		self.addStep(reconfig.ReconfigBuildmasterStep(self.buildBotConfig, self.projectConfig, True, haltOnFailure=True, **BuildTriggerFactory.reconfigDict))
		self.addStep(trigger.Trigger(schedulerNames=self._triggerableNames(), updateSourceStamp=True, waitForFinish=True, **BuildTriggerFactory.triggerDict))
		self.addStep(reconfig.ReconfigBuildmasterStep(self.buildBotConfig, self.projectConfig, False, **BuildTriggerFactory.resetDict))		

