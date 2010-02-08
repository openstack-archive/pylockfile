from __future__ import with_statement

import lockfile
from compliancetest import _ComplianceTest

class ComplianceTest(_ComplianceTest):
    def _lock_wait_unlock(self, event1, event2):
        """Lock from another thread.  Helper for tests."""
        with lockfile.FileLock(self._testfile()):
            event1.set()  # we're in,
            event2.wait() # wait for boss's permission to leave

    def test_enter(self):
        with lockfile.FileLock(self._testfile()):
            assert lock.is_locked()
        assert not lock.is_locked()
