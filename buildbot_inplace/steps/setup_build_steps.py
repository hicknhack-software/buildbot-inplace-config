from buildbot.process.buildstep import LoggingBuildStep, SUCCESS
from buildbot.steps.shell import ShellCommand
from buildbot.steps.shellsequence import ShellSequence
from twisted.internet import defer

from .setup import SetupStep
from .configured_step_mixin import ConfiguredStepMixin


class SetupBuildSteps(LoggingBuildStep, ConfiguredStepMixin):

    def __init__(self, config, *args, **kwargs):
        self.global_config = config
        super(SetupBuildSteps, self).__init__(*args, **kwargs)

    @defer.inlineCallbacks
    def run(self):
        inplace_config = yield self.get_inplace_config()
        profile = inplace_config.profile_named_get(self.build.properties['inplace_profile'])
        env = {}

        for setup in profile.setups:
            desc = "Preparing %s" % setup
            prepare_dict = dict(name=desc, description=desc, descriptionDone=desc)
            self._addStep(SetupStep(setup, config=self.global_config, env=env, **prepare_dict))

        profile_commands = inplace_config.profile_commands(profile)
        for pc in profile_commands:
            shell_dict = dict(name=pc.name, description=pc.name, descriptionDone=pc.name)
            if len(pc.commands) == 1:
                self._addStep(ShellCommand(command=pc.commands[0], env=env, **shell_dict))
            else:
                self._addStep(ShellSequence(pc.commands, env=env, **shell_dict))

        defer.returnValue(SUCCESS)

    def _addStep(self, step):
        build = self.build
        step.setBuild(build)
        step.setWorker(build.workerforbuilder.worker)
        build.steps.append(step)
