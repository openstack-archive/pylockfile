from __future__ import with_statement

import lockfile
from compliancetest import _ComplianceTest

class ComplianceTest(_ComplianceTest):
    def _lock_wait_unlock(self, event1, event2):
        """Lock from another thread.  Helper for tests."""
        with lockfile.LockFile(self._testfile()):
            event1.set()  # we're in,
            event2.wait() # wait for boss's permission to leave

    def test_enter(self):
        with lockfile.LockFile(self._testfile()) as lock:
            assert lock.is_locked()
        assert not lock.is_locked()
