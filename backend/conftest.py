"""Root conftest — re-exports fixtures from the tests package.

pytest automatically discovers this file and makes all fixtures from
``tests/conftest.py`` available to every test module.
"""

from tests.conftest import *  # noqa: F401, F403
