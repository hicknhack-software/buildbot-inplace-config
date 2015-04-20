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

import glob
import os
import yaml

from buildbot.master import config as masterConfig
from buildbot.plugins import buildslave, util, schedulers

from ..factories import reconfig
from ..common.config import BuildbotConfigurationWrapper, SlaveInformation, ProjectConfiguration

class SlaveLoader:

	@staticmethod
	def load(bbConfig, path):
		files = glob.glob( os.path.join(path, '*.yml') )
		if not files:
			raise Exception("No slaves found in '%s'!" % path)
		
		slaveNames = []

		for slaveFile in files:
			y = yaml.safe_load(open(slaveFile).read())
			
			bbConfig.registerSlaveInformation(SlaveInformation(**y))
			bbConfig.addSlave(buildslave.BuildSlave(y['name'], y['password']))

			slaveNames.append(y['name'])

		return slaveNames
    	
class ProjectLoader:
	#TODO: create different types of scheduler
	@staticmethod
	def _createForceScheduler(projectName):
		return schedulers.ForceScheduler(
				name='Force_%s_Builds' % projectName, 
				builderNames=['%s_Builder' % projectName]
			)

	@staticmethod
	def _createTriggerBuilderConfig(bbConfig, slaveNames, projectConfig):
		return masterConfig.BuilderConfig(
				name='%s_Builder' % projectInformation['name'],
				slavenames=slaveNames,
				factory=reconfig.BuildTriggerFactory(
						bbConfig,
						projectConfig
					)
			)

	@staticmethod
	def load(bbConfig, path, slaveNames):
		files = glob.glob( os.path.join(path, '*.yml') )
		if not files:
			raise Exception('No projects found in %s!' % path)
		
		bbConfig.addBuilder(masterConfig.BuilderConfig(name='DummyBuilder', slavenames=slaveNames, factory=util.BuildFactory()))
		bbConfig.addScheduler(schedulers.ForceScheduler(name='Force_Dummy_Build', builderNames=['DummyBuilder']))

		for project in files:
			y = yaml.safe_load(open(project).read())

			try:
				projectConfig = ProjectConfiguration( 
					projectInformation['name'],
					projectInformation['repoUrl'],
					projectInformation['repoType'],
					projectInformation['repoUser'],
					projectInformation['repoPassword'] 
				)

				bbConfig.addBuilder(ProjectLoader._createTriggerBuilderConfig(bbConfig, slaveNames, projectConfig))
				bbConfig.addScheduler(ProjectLoader._createForceScheduler(projectConfig.projectName))

			except:
				raise Exception("Malformed project description!")
			
