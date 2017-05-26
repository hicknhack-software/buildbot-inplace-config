# Buildbot Inplace Config

https://github.com/hicknhack-software/buildbot-inplace-config

This project tries to simplify the Buildbot master.cfg and enables each project to carry it's own build instructions.

## Usage

This plugin requires Buildbot 0.9.x
Download the files from this repository to your Buildbot master.

Example master.cfg
```python
# make buildbot_inplace available
import sys
sys.path.append('inplace')
from buildbot_inplace import InplaceConfig

# allow reconfiguration
import buildbot_inplace
reload(buildbot_inplace)

# use InplaceConfig instead of a bare dict
c = BuildmasterConfig = InplaceConfig()

# projects and workers are loaded from these directories
c.load_workers('workers')
c.load_projects('projects')

# all your normal buildbot configurations
c['protocols'] = {'pb': dict(port=9989)}
c['status'] = []

c['title'] = "Test Buildmaster"
c['titleURL'] = "https://www.github.com"

c['buildbotURL'] = "http://127.0.0.1:8020/"
c['www'] = dict(port=8020, plugins=dict(waterfall_view={}, console_view={}))

c['db'] = {'db_url': "sqlite:///state.sqlite"}

# run the inplace setup
c.setup_inplace()
```

Now you need worker and project configurations.

We use Ansible and custom roles to setup our Buildbot workers.
A configuration looks like this:
```yaml
name: 'testworker' # name of the worker that appears on Buildbot
password: 'test' # shared secret to authenticate on Buildbot
shell: 'bash' # shell type 'bash' or 'cmd'
platforms: ['Linux', 'Ubuntu', 'Ubuntu-14.04', 'Ubuntu1404'] # list of tags that match the platform
setupDir: '~/scripts' # folder where setup scripts reside
setups: ['qt530_gcc490'] # name of setup tags which are also the script names excluding the suffix .bat or .sh
```

For each project we need a trigger config file
```yaml
name: 'Twofold-Qt' # project name used as basis for Buildbot builders
repoType: 'git' # repository type (options: svn, git)
repoUrl: 'https://github.com/hicknhack-software/Twofold-Qt.git'
repoBranch: 'develop' # git only, HEAD is default.
repoUser: ''
repoPassword: ''
```

If you need more complex authentication, for example on submodules you can supply these by adding them in the config as well. Currently, this only works for Git repositories.
```yaml
repoCredentials:
	- url: 'https://github.com'
	  user: 'username'
	  password: 'password'
```


This should be all very straight forward.
The real magic happens in the project. You just add a `.buildbot.yml` file to the root of your repository.
This should look like this:
```yaml
# each profile will become a build if a proper worker is found
profiles:
- name: "Linux Qt5.3 GCC 4.8" # name of the profile that apears in Buildbot
  platform: Ubuntu1404 # the platform tag that a worker has to have
  commands: std # key used in the action (see below)
  setup: ['qt53_gcc48'] # setup tags a worker has to match
                        # these are also the names of setup scripts that are executed before the build actions start

# each action is executed for each profile
actions:
- name: "Prepare" # name of the action that appears in Buildbot
  std: 'make' # actions for the command key of the profile
  msvc: 'nmake.exe'
  mingw: 'mingw32-make.exe'

# actions can define products that will be pushed back to the master
# products can be a file name or a list of file
- name: "Build Products"
  std:
  	commands: 'make'
  	products: 'product.tar.gz'
  mscv:
  	commands: 'nmake.exe' 
  	products:
  		- 'productA.zip'
  		- 'productB.zip'

# for more complex products, a command that returns the list of files to stdout can be used
- name: "Build Products"
  std:
  	commands: 'make'
  	products_command: 'echo product.tar.gz'
```

See "Twofold buildbot.yml":https://github.com/hicknhack-software/Twofold-Qt/blob/develop/.buildbot.yml for a complete example.

## Features

* each project carries it's build instructions
* platform and setup tags for build worker matching
* support for git projects

## Releases

1.0 - to be done

## Roadmap

* stabilize the system
* improve error handling
* Subversion projects
* project and central notification configuration

... and all your crazy ideas.

Pull requests are always welcome.

# License

This project is Apache 2.0 License.
Please read the LICENSE file