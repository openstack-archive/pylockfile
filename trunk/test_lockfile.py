import os
import threading

import lockfile

class ComplianceTest(object):
    def __init__(self):
        self.saved_class = lockfile.FileLock

    def setup(self):
        lockfile.FileLock = self.class_to_test

    def teardown(self):
        tf = _testfile()
        if os.path.isdir(tf):
            shutil.rmtree(tf)
        elif os.path.isfile(tf):
            os.unlink(tf)
        lockfile.FileLock = self.saved_class

    def test_acquire_basic(self):
        # As simple as it gets.
        lock = lockfile.FileLock(_testfile())
        lock.acquire()
        assert lock.is_locked()
        lock.release()
        assert not lock.is_locked()

    def test_acquire_no_timeout(self):
        # No timeout test
        e1, e2 = threading.Event(), threading.Event()
        t = _in_thread(_lock_wait_unlock, e1, e2)
        e1.wait()         # wait for thread t to acquire lock
        lock2 = lockfile.FileLock(_testfile())
        assert lock2.is_locked()
        assert not lock2.i_am_locking()

        try:
            lock2.acquire(timeout=-1)
        except lockfile.AlreadyLocked:
            pass
        else:
            lock2.release()
            raise AssertionError, ("did not raise AlreadyLocked in thread %s" %
                                   threading.currentThread().getName())

        e2.set()          # tell thread t to release lock
        t.join()

    def test_acquire_with_timeout(self):
        # Timeout test
        e1, e2 = threading.Event(), threading.Event()
        t = _in_thread(_lock_wait_unlock, e1, e2)
        e1.wait()                        # wait for thread t to acquire filelock
        lock2 = lockfile.FileLock(_testfile())
        assert lock2.is_locked()
        try:
            lock2.acquire(timeout=0.1)
        except lockfile.LockTimeout:
            pass
        else:
            lock2.release()
            raise AssertionError, ("did not raise LockTimeout in thread %s" %
                                   threading.currentThread().getName())

        e2.set()
        t.join()

    def test_release_basic(self):
        lock = lockfile.FileLock(_testfile())
        lock.acquire()
        assert lock.is_locked()
        lock.release()
        assert not lock.is_locked()
        assert not lock.i_am_locking()
        try:
            lock.release()
        except lockfile.NotLocked:
            pass
        except lockfile.NotMyLock:
            raise AssertionError, ('unexpected exception: %s' %
                                   lockfile.NotMyLock)
        else:
            raise AssertionError, 'erroneously unlocked file'

    def test_release_threaded(self):
        e1, e2 = threading.Event(), threading.Event()
        t = _in_thread(_lock_wait_unlock, e1, e2)
        e1.wait()
        lock2 = lockfile.FileLock(_testfile())
        assert lock2.is_locked()
        assert not lock2.i_am_locking()
        try:
            lock2.release()
        except lockfile.NotMyLock:
            pass
        else:
            raise AssertionError, ('erroneously unlocked a file locked'
                                   ' by another thread.')
        e2.set()
        t.join()

    def test_is_locked(self):
        lock = lockfile.FileLock(_testfile())
        lock.acquire()
        assert lock.is_locked()
        lock.release()
        assert not lock.is_locked()

    def test_i_am_locking(self):
        lock1 = lockfile.FileLock(_testfile(), threaded=False)
        lock1.acquire()
        assert lock1.is_locked()
        lock2 = lockfile.FileLock(_testfile())
        assert lock1.i_am_locking()
        assert not lock2.i_am_locking()
        try:
            lock2.acquire(timeout=2)
        except lockfile.LockTimeout:
            lock2.break_lock()
            assert not lock2.is_locked()
            assert not lock1.is_locked()
            lock2.acquire()
        else:
            raise AssertionError('expected LockTimeout...')
        assert not lock1.i_am_locking()
        assert lock2.i_am_locking()
        lock2.release()

    def test_break_lock(self):
        lock = lockfile.FileLock(_testfile())
        lock.acquire()
        assert lock.is_locked()
        lock2 = lockfile.FileLock(_testfile())
        assert lock2.is_locked()
        lock2.break_lock()
        assert not lock2.is_locked()
        try:
            lock.release()
        except lockfile.NotLocked:
            pass
        else:
            raise AssertionError('break lock failed')

    def test_enter(self):
        lock = lockfile.FileLock(_testfile())
        with lock:
            assert lock.is_locked()
        assert not lock.is_locked()

def _in_thread(func, *args, **kwargs):
    """Execute func(*args, **kwargs) after dt seconds. Helper for tests."""
    def _f():
        func(*args, **kwargs)
    t = threading.Thread(target=_f, name='/*/*')
    t.start()
    return t

def _testfile():
    """Return platform-appropriate file.  Helper for tests."""
    import tempfile
    return os.path.join(tempfile.gettempdir(), 'trash-%s' % os.getpid())

def _lock_wait_unlock(event1, event2):
    """Lock from another thread.  Helper for tests."""
    with lockfile.FileLock(_testfile()):
        event1.set()  # we're in,
        event2.wait() # wait for boss's permission to leave

class TestLinkFileLock(ComplianceTest):
    class_to_test = lockfile.LinkFileLock

class TestMkdirFileLock(ComplianceTest):
    class_to_test = lockfile.MkdirFileLock

try:
    import sqlite3
except ImportError:
    pass
else:
    class TestSQLiteFileLock(ComplianceTest):
        class_to_test = lockfile.SQLiteFileLock
