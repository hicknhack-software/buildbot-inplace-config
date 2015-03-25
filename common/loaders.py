import glob
import os
import yaml

from buildbot.master import config as masterConfig
from buildbot.plugins import buildslave, util, schedulers

from ..factories import reconfig
from ..common.config import BuildbotConfigurationWrapper, SlaveInformation

class SlaveLoader:

	@staticmethod
	def load(bbConfig, path):
		files = glob.glob( os.path.join(path, '*.slave') )
		if not files:
			raise Exception("No slaves found in '%s'!" % path)
		
		slaveNames = []

		for slaveFile in files:
			y = yaml.safe_load(open(slaveFile).read())
			
			bbConfig.registerSlaveInformation(SlaveInformation(**y))
			bbConfig.addSlave(buildslave.BuildSlave(y["name"], y["password"]))

			slaveNames.append(y["name"])

		return slaveNames
    	
class ProjectLoader:
	#TODO: create different types of scheduler
	@staticmethod
	def _createForceScheduler(projectName):
		return schedulers.ForceScheduler(
				name="Force_%s_Builds" % projectName, 
				builderNames=["%s_Builder" % projectName]
			)

	@staticmethod
	def _createTriggerBuilderConfig(bbConfig, slaveNames, **projectInformation):
		return masterConfig.BuilderConfig(
				name="%s_Builder" % projectInformation["name"],
				slavenames=slaveNames,
				factory=reconfig.BuildTriggerFactory(
						bbConfig,
						projectInformation["name"],
						projectInformation["repoUrl"],
						projectInformation["repoType"]
					)
			)

	@staticmethod
	def load(bbConfig, path, slaveNames):
		files = glob.glob( os.path.join(path, '*.project') )
		if not files:
			raise Exception("No projects found in '%s'!" % path)
		
		bbConfig.addBuilder(masterConfig.BuilderConfig(name="DummyBuilder", slavenames=slaveNames, factory=util.BuildFactory()))
		bbConfig.addScheduler(schedulers.ForceScheduler(name="Force_Dummy_Build", builderNames=["DummyBuilder"]))

		for project in files:
			y = yaml.safe_load(open(project).read())

			projectInformation = {
				'name': y["name"],
				'repoUrl': y["repoUrl"],
				'repoType': y["repoType"],
			}

			bbConfig.addBuilder(ProjectLoader._createTriggerBuilderConfig(bbConfig, slaveNames, **projectInformation))
			bbConfig.addScheduler(ProjectLoader._createForceScheduler(projectInformation["name"]))
			
