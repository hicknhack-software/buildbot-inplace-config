""" Buildbot inplace config
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
"""
from Queue import Queue
from buildbot.config import MasterConfig
from buildbot.status.results import FAILURE
from buildbot.steps.master import MasterShellCommand
from .success import ShowStepIfSuccessful

class ProfileNotFulfilledException(Exception):
    pass

def create_master_config(config_dict):
    try:
        master_config = MasterConfig()
        filename = None
        master_config.load_global(filename, config_dict)
        master_config.load_validation(filename, config_dict)
        master_config.load_db(filename, config_dict)
        master_config.load_mq(filename, config_dict)
        master_config.load_metrics(filename, config_dict)
        master_config.load_caches(filename, config_dict)
        master_config.load_schedulers(filename, config_dict)
        master_config.load_builders(filename, config_dict)
        master_config.load_workers(filename, config_dict)
        master_config.load_change_sources(filename, config_dict)
        master_config.load_status(filename, config_dict)
        master_config.load_user_managers(filename, config_dict)
        master_config.load_www(filename, config_dict)
        master_config.load_services(filename, config_dict)
        # run some sanity checks
        master_config.check_single_master()
        master_config.check_schedulers()
        master_config.check_locks()
        master_config.check_builders()
        master_config.check_status()
        master_config.check_horizons()
        master_config.check_ports()
    except Exception as e:
        raise Exception("Could not reconfigure Buildbot: " + str(e))
    return master_config


class ReconfigBuildmasterStep(MasterShellCommand):
    """ A Step that reconfigures the Buildmaster."""

    COMMAND = ["echo", "Reconfigured Master"]

    def __init__(self, config, project, update_from_project, **kwargs):
        self.config = config
        self.project = project
        self.from_project = update_from_project
        MasterShellCommand.__init__(self,
                                    command=self.COMMAND,
                                    hideStepIf=ShowStepIfSuccessful,
                                    **kwargs)

    def start(self):
        try:
            self.config.setup_project_inplace(self.project)
        except ProfileNotFulfilledException as e:
            self.addCompleteLog("errorlog", "Failing: %s" % str(e))
            return FAILURE

        if self.from_project:
            master_config = create_master_config(self.config)
            self.master.config = master_config
            for svc in self.master.workers.services:
                svc.configured = False
            self.master.reconfigServiceWithBuildbotConfig(master_config)
        else:
            self.master.reconfig()

        return MasterShellCommand.start(self)
