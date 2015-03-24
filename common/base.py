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

class NamedInstance(object):
	def __init__(self, **kwargs):
		self.name = kwargs["name"]

	def __hash__(self):
		return hash(self.name)

	def __eq__(self, other):
		return self.name == other.name

	def __repr__(self):
		return self.name

class Platform(NamedInstance):

	def __init__(self, **kwargs):
		NamedInstance.__init__(self, **kwargs)

	def __repr__(self):
		return self.name

class Dependency(NamedInstance):

	def __init__(self, name):
		super(Dependency, self).__init__(name=name)

class Profile(NamedInstance):

	def __init__(self, **kwargs):
		self.platform = kwargs["platform"]
		self.setup = kwargs["setup"]
		self.commands = kwargs["commands"]
		super(Profile, self).__init__(**kwargs)

class Action(NamedInstance):

	def __init__(self, **kwargs):
		self.commands = kwargs["commands"]
		super(Action, self).__init__(**kwargs)
