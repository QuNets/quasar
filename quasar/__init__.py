"""QUASAR overlay package.

QUASAR extends SimQN with satellite-network abstractions while keeping the
SimQN core package independent.
"""

from quasar.api import QuasarSimulator, QuasarStepResult

__version__ = "0.1.0"

__all__ = ["QuasarSimulator", "QuasarStepResult", "__version__"]
