import os
import threading

from lockfile import *

def _acquire():
    # As simple as it gets.
    lock = FileLock(_testfile())
    lock.acquire()
    assert lock.is_locked()
    lock.release()
    assert not lock.is_locked()

    # No timeout test
    e1, e2 = threading.Event(), threading.Event()
    t = _in_thread(_lock_wait_unlock, e1, e2)
    e1.wait()         # wait for thread t to acquire lock
    lock2 = FileLock(_testfile())
    assert lock2.is_locked()
    assert not lock2.i_am_locking()
    
    try:
        lock2.acquire(timeout=-1)
    except AlreadyLocked:
        pass
    else:
        lock2.release()
        raise AssertionError, ("did not raise AlreadyLocked in thread %s" %
                               threading.currentThread().getName())

    e2.set()          # tell thread t to release lock
    t.join()

    # Timeout test
    e1, e2 = threading.Event(), threading.Event()
    t = _in_thread(_lock_wait_unlock, e1, e2)
    e1.wait()                        # wait for thread t to acquire filelock
    lock2 = FileLock(_testfile())
    assert lock2.is_locked()
    try:
        lock2.acquire(timeout=0.1)
    except LockTimeout:
        pass
    else:
        lock2.release()
        raise AssertionError, ("did not raise LockTimeout in thread %s" %
                               threading.currentThread().getName())
    
    e2.set()
    t.join()

def _release():
    lock = FileLock(_testfile())
    lock.acquire()
    assert lock.is_locked()
    lock.release()
    assert not lock.is_locked()
    assert not lock.i_am_locking()
    try:
        lock.release()
    except NotLocked:
        pass
    except NotMyLock:
        raise AssertionError, 'unexpected exception: %s' % NotMyLock
    else:
        raise AssertionError, 'erroneously unlocked file'

    e1, e2 = threading.Event(), threading.Event()
    t = _in_thread(_lock_wait_unlock, e1, e2)
    e1.wait()
    lock2 = FileLock(_testfile())
    assert lock2.is_locked()
    assert not lock2.i_am_locking()
    try:
        lock2.release()
    except NotMyLock:
        pass
    else:
        raise AssertionError, ('erroneously unlocked a file locked'
                               ' by another thread.')
    e2.set()
    t.join()

def _is_locked():
    lock = FileLock(_testfile())
    lock.acquire()
    assert lock.is_locked()
    lock.release()
    assert not lock.is_locked()

def _i_am_locking():
    lock1 = FileLock(_testfile(), threaded=False)
    lock1.acquire()
    assert lock1.is_locked()
    lock2 = FileLock(_testfile())
    assert lock1.i_am_locking()
    assert not lock2.i_am_locking()
    try:
        lock2.acquire(timeout=2)
    except LockTimeout:
        lock2.break_lock()
        assert not lock2.is_locked()
        assert not lock1.is_locked()
        lock2.acquire()
    else:
        raise AssertionError('expected LockTimeout...')
    assert not lock1.i_am_locking()
    assert lock2.i_am_locking()
    lock2.release()

def _break_lock():
    lock = FileLock(_testfile())
    lock.acquire()
    assert lock.is_locked()
    lock2 = FileLock(_testfile())
    assert lock2.is_locked()
    lock2.break_lock()
    assert not lock2.is_locked()
    try:
        lock.release()
    except NotLocked:
        pass
    else:
        raise AssertionError('break lock failed')

def _enter():
    lock = FileLock(_testfile())
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
    with FileLock(_testfile()):
        event1.set()  # we're in,
        event2.wait() # wait for boss's permission to leave

def test_variants():
    global FileLock

    def _helper():
        _acquire()
        _release()
        _is_locked()
        _i_am_locking()
        _break_lock()
        _enter()

    if hasattr(os, "link"):
        FileLock, _Lock = LinkFileLock, FileLock
        try:
            _helper()
        finally:
            FileLock = _Lock

    if hasattr(os, "mkdir"):
        FileLock, _Lock = MkdirFileLock, FileLock
        try:
            _helper()
        finally:
            FileLock = _Lock

    try:
        import sqlite3
    except ImportError:
        pass
    else:
        FileLock, _Lock = SQLiteFileLock, FileLock
        try:
            _helper()
        finally:
            FileLock = _Lock
