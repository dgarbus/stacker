import logging

from .base import BaseAction
from .. import exceptions

logger = logging.getLogger(__name__)


class Action(BaseAction):
    """Get information on CloudFormation stacks.

    Displays the outputs for the set of CloudFormation stacks.

    """

    def run(self, *args, **kwargs):
        logger.info('Outputs for stacks: %s', self.context.get_fqn())
        for stack in self.context.get_stacks():
            try:
                provider_stack = self.provider.get_stack(stack.fqn)
            except exceptions.StackDoesNotExist:
                logger.info('Stack "%s" does not exist.' % (stack.fqn,))
                continue

            logger.info('%s:', stack.fqn)
            for output in provider_stack.outputs:
                logger.info('\t%s: %s', output.key, output.value)
