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

	KnownLists = ["path"]

	def __init__(self, environmentDict, listDelimiter=":"):
		self.environmentDict = environmentDict
		self.listDelimiter = listDelimiter

	def _maybeAppend(self, key, value):
		if key.lower() in EnvironmentParser.KnownLists:
			old = self.environmentDict[key]
			self.environmentDict[key] = self.listDelimiter.join([old, value])
		else:
			self.environmentDict[key] = value

	def _parseLine(self, line):
		if "=" in line:
			key, value = line.split("=", 1)
			if not key in self.environmentDict:
				self.environmentDict[key] = value
				return
 
			self._maybeAppend(key, value)

	def _retrieveEnvironment(self):
		while True:
			stream, line = yield
			if stream == 'o':
				self._parseLine(line)
