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
from glob import glob
from os import path
from twisted.python import log
from yaml import safe_load
from buildbot.buildslave import BuildSlave


def _normalize_path(p):
    s = p.replace("\\", "/")
    if s[-1] is not "/":
        s += "/"
    return s

class Slave(dict):
    @property
    def name(self):
        return self['name']

    @property
    def password(self):
        return self['password']

    @property
    def shell(self):
        return self['shell']

    @property
    def setup_dir(self):
        return _normalize_path(self['setupDir'])

    @property
    def platforms(self):
        return self['platforms']

    @property
    def setups(self):
        return self['setups']

    def build_slave(self):
        return BuildSlave(self.name, self.password)

    @staticmethod
    def load(slaves_dir, inplace_slaves, slaves):
        files = glob(path.join(slaves_dir, '*.yml'))
        if not files:
            raise Exception("No slaves found in '%s'!" % slaves_dir)

        slaves.clear()
        inplace_slaves.clear()
        for f in files:
            s = open(f, 'r')
            slave_dict = safe_load(s)
            s.close()
            if not isinstance(slave_dict, dict):
                continue

            inplace_slave = Slave(**slave_dict)
            inplace_slaves.named_set(inplace_slave)
            log.msg("Registered Slave '%s' on %s with setups %s" %
                    (inplace_slave.name, ', '.join(inplace_slave.platforms), ', '.join(inplace_slave.setups)),
                    system='Inplace Config')
            slaves.named_set(inplace_slave.build_slave())
