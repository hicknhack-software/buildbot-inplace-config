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

from buildbot.status.results import SUCCESS

OVERRIDE_HIDE_IF = False
ShowStepIfSuccessful = (lambda results, s: results is SUCCESS and not OVERRIDE_HIDE_IF)

def triggerableName(projectName, platformName):
	return "%s_%s_Triggerable" % (projectName, platformName)

class EnvironmentParser:

	def __init__(self, environmentDict):
		self.environmentDict = environmentDict

	def _initEnvironment(self):
		while True:
			stream, line = yield
			if stream == 'o':
				if "=" in line:
					key, value = line.split("=", 1)
					self.environmentDict[key] = value

	def _diffEnvironment(self):
		while True:
			stream, line = yield
	        if stream == 'o':
				if "=" in line:
					key, value = line.split("=", 1)
					if key in self.environmentDict:
						self.environmentDict.remove(key)
					else:
						self.environmentDict[key] = value	