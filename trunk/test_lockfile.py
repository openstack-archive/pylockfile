import os
import threading

from lockfile import *

def test_acquire():
    """
    >>> # As simple as it gets.
    >>> lock = FileLock(_testfile())
    >>> lock.acquire()
    >>> lock.release()

    >>> # No timeout test
    >>> e1, e2 = threading.Event(), threading.Event()
    >>> t = _in_thread(_lock_wait_unlock, e1, e2)
    >>> e1.wait()         # wait for thread t to acquire lock
    >>> lock2 = FileLock(_testfile())
    >>> lock2.is_locked()
    True
    >>> lock2.i_am_locking()
    False
    >>> try:
    ...   lock2.acquire(timeout=-1)
    ... except AlreadyLocked:
    ...   pass
    ... except Exception, e:
    ...   print 'unexpected exception', repr(e)
    ... else:
    ...   print 'thread', threading.currentThread().getName(),
    ...   print 'erroneously locked an already locked file.'
    ...   lock2.release()
    ...
    >>> e2.set()          # tell thread t to release lock
    >>> t.join()

    >>> # Timeout test
    >>> e1, e2 = threading.Event(), threading.Event()
    >>> t = _in_thread(_lock_wait_unlock, e1, e2)
    >>> e1.wait() # wait for thread t to acquire filelock
    >>> lock2 = FileLock(_testfile())
    >>> lock2.is_locked()
    True
    >>> try:
    ...   lock2.acquire(timeout=0.1)
    ... except LockTimeout:
    ...   pass
    ... except Exception, e:
    ...   print 'unexpected exception', repr(e)
    ... else:
    ...   lock2.release()
    ...   print 'thread', threading.currentThread().getName(),
    ...   print 'erroneously locked an already locked file.'
    ...
    >>> e2.set()
    >>> t.join()
    """
    pass

def test_release():
    """
    >>> lock = FileLock(_testfile())
    >>> lock.acquire()
    >>> lock.release()
    >>> lock.is_locked()
    False
    >>> lock.i_am_locking()
    False
    >>> try:
    ...   lock.release()
    ... except NotLocked:
    ...   pass
    ... except NotMyLock:
    ...   print 'unexpected exception', NotMyLock
    ... except Exception, e:
    ...   print 'unexpected exception', repr(e)
    ... else:
    ...   print 'erroneously unlocked file'

    >>> e1, e2 = threading.Event(), threading.Event()
    >>> t = _in_thread(_lock_wait_unlock, e1, e2)
    >>> e1.wait()
    >>> lock2 = FileLock(_testfile())
    >>> lock2.is_locked()
    True
    >>> lock2.i_am_locking()
    False
    >>> try:
    ...   lock2.release()
    ... except NotMyLock:
    ...   pass
    ... except Exception, e:
    ...   print 'unexpected exception', repr(e)
    ... else:
    ...   print 'erroneously unlocked a file locked by another thread.'
    ...
    >>> e2.set()
    >>> t.join()
    """
    pass

def test_is_locked():
    """
    >>> lock = FileLock(_testfile())
    >>> lock.acquire()
    >>> lock.is_locked()
    True
    >>> lock.release()
    >>> lock.is_locked()
    False
    """
    pass

def test_i_am_locking():
    """
    >>> lock1 = FileLock(_testfile(), threaded=False)
    >>> lock1.acquire()
    >>> lock2 = FileLock(_testfile())
    >>> lock1.i_am_locking()
    True
    >>> lock2.i_am_locking()
    False
    >>> try:
    ...   lock2.acquire(timeout=2)
    ... except LockTimeout:
    ...   lock2.break_lock()
    ...   lock2.is_locked()
    ...   lock1.is_locked()
    ...   lock2.acquire()
    ... else:
    ...   print 'expected LockTimeout...'
    ...
    False
    False
    >>> lock1.i_am_locking()
    False
    >>> lock2.i_am_locking()
    True
    >>> lock2.release()
    """
    pass

def test_break_lock():
    """
    >>> lock = FileLock(_testfile())
    >>> lock.acquire()
    >>> lock2 = FileLock(_testfile())
    >>> lock2.is_locked()
    True
    >>> lock2.break_lock()
    >>> lock2.is_locked()
    False
    >>> try:
    ...   lock.release()
    ... except NotLocked:
    ...   pass
    ... except Exception, e:
    ...   print 'unexpected exception', repr(e)
    ... else:
    ...   print 'break lock failed'
    """
    pass

def test_enter():
    """
    >>> lock = FileLock(_testfile())
    >>> with lock:
    ...   lock.is_locked()
    ...
    True
    >>> lock.is_locked()
    False
    """
    pass

def test_LinkFileLock_acquire():
    """
    >>> d = _testfile()
    >>> os.mkdir(d)
    >>> os.chmod(d, 0444)
    >>> try:
    ...   lock = LinkFileLock(os.path.join(d, 'test'))
    ...   try:
    ...     lock.acquire()
    ...   except LockFailed:
    ...     pass
    ...   else:
    ...     lock.release()
    ...     print 'erroneously locked', os.path.join(d, 'test')
    ... finally:
    ...   os.chmod(d, 0664)
    ...   os.rmdir(d)
    """
    pass

def _in_thread(func, *args, **kwargs):
    """Execute func(*args, **kwargs) after dt seconds.

    Helper for docttests.
    """
    def _f():
        func(*args, **kwargs)
    t = threading.Thread(target=_f, name='/*/*')
    t.start()
    return t

def _testfile():
    """Return platform-appropriate file.

    Helper for doctests.
    """
    import tempfile
    return os.path.join(tempfile.gettempdir(), 'trash-%s' % os.getpid())

def _lock_wait_unlock(event1, event2):
    """Lock from another thread.

    Helper for doctests.
    """
    with FileLock(_testfile()):
        event1.set()  # we're in,
        event2.wait() # wait for boss's permission to leave

def _test():
    global FileLock

    import doctest
    import sys

    def test_object(c):
        nfailed = ntests = 0
        for (obj, recurse) in ((c, True),
                               (LockBase, True),
                               (sys.modules["__main__"], False)):
            tests = doctest.DocTestFinder(recurse=recurse).find(obj)
            runner = doctest.DocTestRunner(verbose="-v" in sys.argv)
            tests.sort(key = lambda test: test.name)
            for test in tests:
                f, t = runner.run(test)
                nfailed += f
                ntests += t
        print FileLock.__name__, "tests:", ntests, "failed:", nfailed
        return nfailed, ntests

    nfailed = ntests = 0

    if hasattr(os, "link"):
        FileLock = LinkFileLock
        f, t = test_object(FileLock)
        nfailed += f
        ntests += t

    if hasattr(os, "mkdir"):
        FileLock = MkdirFileLock
        f, t = test_object(FileLock)
        nfailed += f
        ntests += t

    try:
        import sqlite3
    except ImportError:
        print "SQLite3 is unavailable - not testing SQLiteFileLock."
    else:
        print "Testing SQLiteFileLock with sqlite", sqlite3.sqlite_version,
        print "& pysqlite", sqlite3.version
        FileLock = SQLiteFileLock
        f, t = test_object(FileLock)
        nfailed += f
        ntests += t

    print "total tests:", ntests, "total failed:", nfailed

if __name__ == "__main__":
    _test()
