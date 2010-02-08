import lockfile
from compliancetest import _ComplianceTest

class ComplianceTest(_ComplianceTest):
    def _lock_wait_unlock(self, event1, event2):
        """Lock from another thread.  Helper for tests."""
        l = lockfile.FileLock(self._testfile())
        l.acquire()
        try:
            event1.set()  # we're in,
            event2.wait() # wait for boss's permission to leave
        finally:
            l.release()

    def test_enter(self):
        lock = lockfile.FileLock(self._testfile())
        lock.acquire()
        try:
            assert lock.is_locked()
        finally:
            lock.release()
        assert not lock.is_locked()
