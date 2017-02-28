""" Buildbot inplace config
(C) Copyright 2015-2017 HicknHack Software GmbH

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
from twisted.internet import defer
from buildbot.process.buildstep import BuildStep, ShellMixin
from buildbot.process.logobserver import LineConsumerLogObserver


class EnvironmentParser:
    PATH_LISTS = ['path']  # use lowercase here!

    def __init__(self, env_dict, path_delimiter=':'):
        self.env_dict = env_dict
        self.path_delimiter = path_delimiter

    def _store(self, key, value):
        if key.lower() in self.PATH_LISTS:
            values = self.env_dict[key].split(self.path_delimiter) if key in self.env_dict else []
            values += [item for item in value.split(self.path_delimiter) if item not in values]
            self.env_dict[key] = self.path_delimiter.join(values)
        else:
            self.env_dict[key] = value

    def _parse_line(self, line):
        if '=' in line:
            key, value = line.split('=', 1)
            self._store(key, value)

    def retrieve(self):
        while True:
            stream, line = yield
            if stream == 'o':
                self._parse_line(line)


class SetupStep(ShellMixin, BuildStep):
    """A Step that retrieves the environment after a command."""

    SHELL_CONFIG = {
        "cmd": dict(
            path_delimiter=";",
            cmd_delimiter="&",
            start=["cmd", "/c"],
            echo_env="set",
            prefix="",
            suffix=".bat",
        ),
        "bash": dict(
            path_delimiter=":",
            cmd_delimiter=";",
            start=["bash", "-c"],
            echo_env="env",
            prefix=". ",
            suffix=".sh",
        )
    }
    FALLBACK_SHELL = "bash"

    def __init__(self, setup, config, env, **kwargs):
        self.setup = setup
        self.global_config = config
        self.env_dict = env
        self.consumer = None
        kwargs = self.setupShellMixin(kwargs, prohibitArgs=['command'])
        BuildStep.__init__(self, **kwargs)

    @defer.inlineCallbacks
    def run(self):
        worker = self.global_config.inplace_workers.named_get(self.getWorkerName())
        shell_config = self._shell_config(worker)
        remote_cmd = self._command(worker, shell_config)
        cmd = yield self.makeRemoteShellCommand(command=remote_cmd, collectStdout=True, stdioLogName="envLog")
        self.consumer = EnvironmentParser(self.env_dict, shell_config['path_delimiter'])
        self.addLogObserver('envLog', LineConsumerLogObserver(self.consumer.retrieve))
        yield self.runCommand(cmd)
        yield defer.returnValue(cmd.results())

    def _shell_config(self, worker_info):
        shell = worker_info.shell
        if shell not in self.SHELL_CONFIG:
            shell = self.FALLBACK_SHELL
        return self.SHELL_CONFIG[shell]

    def _command(self, worker_info, shell_config):
        setup = ''.join([shell_config['prefix'], worker_info.setup_dir, self.setup, shell_config['suffix']])
        shell = shell_config['start']
        return shell + [shell_config['cmd_delimiter'].join([setup, shell_config['echo_env']])]
