
"""
lockfile.py - Platform-independent advisory file locks.

Locking is done on a per-thread basis instead of a per-process basis.

Usage:

>>> lock = FileLock(_testfile())
>>> try:
...     lock.acquire()
... except AlreadyLocked:
...     print _testfile(), 'is locked already.'
... except LockFailed:
...     print _testfile(), 'can\\'t be locked.'
... else:
...     print 'got lock'
got lock
>>> lock.release()

>>> lock = FileLock(_testfile())
>>> with lock:
...    print lock.is_locked()
True
>>> print lock.is_locked()
False

Exceptions:

    Error - base class for other exceptions
        LockError - base class for all locking exceptions
            AlreadyLocked - Another thread or process already holds the lock
            LockFailed - Lock failed for some other reason
        UnlockError - base class for all unlocking exceptions
            AlreadyUnlocked - File was not locked.
            NotMyLock - File was locked but not by the current thread/process

To do:
    * Write more test cases
      - test cases where threaded == False
      - test case(s) for i_am_locking()
      - verify that all lines of code are executed
    * Actually test MkdirFileLock class on Windows
"""

from __future__ import division
from __future__ import with_statement

import socket
import os
import threading
import time
import errno

class Error(Exception):
    """
    Base class for other exceptions.

    >>> try:
    ...   raise Error
    ... except Exception:
    ...   pass
    """
    pass

class LockError(Error):
    """
    Base class for error arising from attempts to acquire the lock.

    >>> try:
    ...   raise LockError
    ... except Error:
    ...   pass
    """
    pass

class LockTimeout(LockError):
    """Raised when lock creation fails within a user-defined period of time.

    >>> try:
    ...   raise LockTimeout
    ... except LockError:
    ...   pass
    """
    pass

class AlreadyLocked(LockError):
    """Some other thread/process is locking the file.

    >>> try:
    ...   raise AlreadyLocked
    ... except LockError:
    ...   pass
    """
    pass

class LockFailed(LockError):
    """Lock file creation failed for some other reason.

    >>> try:
    ...   raise LockFailed
    ... except LockError:
    ...   pass
    """
    pass

class UnlockError(Error):
    """
    Base class for errors arising from attempts to release the lock.

    >>> try:
    ...   raise UnlockError
    ... except Error:
    ...   pass
    """
    pass

class NotLocked(UnlockError):
    """Raised when an attempt is made to unlock an unlocked file.

    >>> try:
    ...   raise NotLocked
    ... except UnlockError:
    ...   pass
    """
    pass

class NotMyLock(UnlockError):
    """Raised when an attempt is made to unlock a file someone else locked.

    >>> try:
    ...   raise NotMyLock
    ... except UnlockError:
    ...   pass
    """
    pass

class _FileLock:
    """Base class for platform-specific lock classes."""
    def __init__(self, path, threaded=True):
        """
        >>> lock = _FileLock(_testfile())
        """
        self.path = path
        self.lock_file = os.path.abspath(path) + ".lock"
        self.hostname = socket.gethostname()
        self.pid = os.getpid()
        if threaded:
            tname = "%s-" % threading.currentThread().getName()
        else:
            tname = ""
        dirname = os.path.dirname(self.lock_file)
        self.unique_name = src = os.path.join(dirname,
                                              "%s.%s%s" % (self.hostname,
                                                           tname,
                                                           self.pid))

    def acquire(self, timeout=None):
        """
        Acquire the lock.

        * If timeout is omitted (or None), wait forever trying to lock the
          file.

        * If timeout > 0, try to acquire the lock for that many seconds.  If
          the lock period expires and the file is still locked, raise
          LockTimeout.

        * If timeout <= 0, raise AlreadyLocked immediately if the file is
          already locked.

        >>> # As simple as it gets.
        >>> lock = FileLock(_testfile())
        >>> lock.acquire()
        >>> lock.release()

        >>> # Simple timeout test.
        >>> x = open(_testfile() + '.lock', 'wb')
        >>> try:
        ...   lock.acquire(timeout=0.4)
        ... except LockTimeout:
        ...   pass
        ... else:
        ...   print 'erroneously locked the file'
        >>> # Simple no timeout test.
        >>> try:
        ...   lock.acquire(timeout=-1)
        ... except LockTimeout:
        ...   print 'erroneously raised LockTimeout'
        ... except AlreadyLocked:
        ...   pass
        ... else:
        ...   print 'erroneously locked the file'
        ...
        >>> x.close()
        >>> os.unlink(_testfile() + '.lock')

        >>> _after(0, _lock_sleep_unlock)
        >>> while not os.path.exists(_testfile() + '.lock'):
        ...   time.sleep(0.05)
        ...
        >>> os.path.exists(_testfile() + '.lock')
        True
        >>> lock2 = FileLock(_testfile())
        >>> lock2.is_locked()
        True
        >>> try:
        ...   lock2.acquire(timeout=-1)
        ... except AlreadyLocked:
        ...   pass
        ... else:
        ...   lock2.release()
        ...   print threading.currentThread().getName(),
        ...   print 'erroneously locked an already locked file.'
        ...
        >>> while threading.activeCount() > 1:
        ...   time.sleep(0.1)

        >>> testdir = os.path.join(os.path.dirname(_testfile()), 'lockdir')
        >>> testfile = os.path.join(testdir, 'trash')
        >>> os.mkdir(testdir)
        >>> try:
        ...   os.mkdir(testdir)
        ... except OSError, err:
        ...   if err.errno != errno.EEXIST:
        ...     raise
        >>> os.chmod(testdir, 0555)
        >>> lock = FileLock(testfile)
        >>> try:
        ...   lock.acquire()
        ... except LockFailed:
        ...   pass
        ... else:
        ...   lock.release()
        ...   print 'erroneously locked an unlockable file'
        ...
        >>> os.chmod(testdir, 0777)
        >>> os.rmdir(testdir)
        """
        pass

    def release(self):
        """
        Release the lock.

        If the file is not locked, raise NotLocked.
        >>> lock = FileLock(_testfile())
        >>> lock.acquire()
        >>> lock.release()
        >>> os.path.exists(lock.lock_file)
        False
        >>> os.path.exists(lock.unique_name)
        False
        >>> try:
        ...   lock.release()
        ... except NotLocked:
        ...   pass
        ... else:
        ...   print 'erroneously unlocked file'

        >>> _after(0, _lock_sleep_unlock)
        >>> while not os.path.exists(_testfile() + '.lock'):
        ...   time.sleep(0.05)
        ...
        >>> os.path.exists(_testfile() + '.lock')
        True
        >>> lock2 = FileLock(_testfile())
        >>> lock2.is_locked()
        True
        >>> try:
        ...   lock2.release()
        ... except NotMyLock:
        ...   pass
        ... else:
        ...   print 'erroneously unlocked a file locked by another thread.'
        ...
        >>> while threading.activeCount() > 1:
        ...   time.sleep(0.1)
        """
        pass

    def is_locked(self):
        """
        Tell whether or not the file is locked.
        >>> lock = FileLock(_testfile())
        >>> lock.acquire()
        >>> lock.is_locked()
        True
        >>> lock.release()
        >>> lock.is_locked()
        False
        """
        pass

    def i_am_locking(self):
        """Return True if this object is locking the file.

        >>> lock1 = FileLock(_testfile(), threaded=False)
        >>> lock1.acquire()
        >>> lock2 = FileLock(_testfile())
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

    def break_lock(self):
        """Remove a lock.  Useful if a locking thread failed to unlock.

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
        ... else:
        ...   print 'break lock failed'
        """
        pass

    def __enter__(self):
        """Context manager support.

        >>> lock = FileLock(_testfile())
        >>> with lock:
        ...   lock.is_locked()
        ...
        True
        >>> lock.is_locked()
        False
        """
        self.acquire()
        return self

    def __exit__(self, *exc):
        """Context manager support.

        >>> 'tested in __enter__'
        'tested in __enter__'
        """
        self.release()

class LinkFileLock(_FileLock):
    """
    Lock access to a file using atomic property of link(2).

    The name of the file to be locked is input.  The lock file will have a
    '.lock' extension added to it.
    """

    def acquire(self, timeout=None):
        try:
            open(self.unique_name, "wb")
        except IOError:
            raise LockFailed

        end_time = time.time()
        if timeout is not None and timeout > 0:
            end_time += timeout

        while True:
            # Try and create a hard link to it.
            try:
                os.link(self.unique_name, self.lock_file)
            except OSError, msg:
                # Link creation failed.  Maybe we've double-locked?
                nlinks = os.stat(self.unique_name).st_nlink
                if nlinks == 2:
                    # The original link plus the one I created == 2.  We're
                    # good to go.
                    return
                else:
                    # Otherwise the lock creation failed.
                    if timeout is not None and time.time() > end_time:
                        os.unlink(self.unique_name)
                        if timeout > 0:
                            raise LockTimeout
                        else:
                            raise AlreadyLocked
                    time.sleep(timeout is not None and timeout/10 or 0.1)
            else:
                # Link creation succeeded.  We're good to go.
                return

    def release(self):
        if not self.is_locked():
            raise NotLocked
        elif not os.path.exists(self.unique_name):
            raise NotMyLock
        os.unlink(self.unique_name)
        os.unlink(self.lock_file)

    def is_locked(self):
        return os.path.exists(self.lock_file)

    def i_am_locking(self):
        return (self.is_locked() and
                os.path.exists(self.unique_name) and
                os.stat(self.unique_name).st_nlink == 2)

    def break_lock(self):
        if os.path.exists(self.lock_file):
            os.unlink(self.lock_file)

class MkdirFileLock(_FileLock):
    """Lock file by creating a directory.

    I can't actually test this implementation on Windows as I don't do
    Windows.
    """
    def __init__(self, path, threaded=True):
        """
        >>> lock = MkdirFileLock(_testfile())
        """
        _FileLock.__init__(self, path)
        if threaded:
            tname = "%s-" % threading.currentThread().getName()
        else:
            tname = ""
        # Lock file itself is a directory.  Place the unique file name into
        # it.
        self.unique_name = src = os.path.join(self.lock_file,
                                              "%s.%s%s" % (self.hostname,
                                                           tname,
                                                           self.pid))

    def acquire(self, timeout=None):
        end_time = time.time()
        if timeout is not None and timeout > 0:
            end_time += timeout

        if timeout is None:
            wait = 0.1
        elif timeout <= 0:
            wait = 0
        else:
            wait = timeout / 10

        while True:
            try:
                os.mkdir(self.lock_file)
            except OSError, err:
                if err.errno == errno.EEXIST:
                    # Already locked.
                    if os.path.exists(self.unique_name):
                        # Already locked by me.
                        return
                    if timeout is not None and time.time() > end_time:
                        if timeout > 0:
                            raise LockTimeout
                        else:
                            # Someone else has the lock.
                            raise AlreadyLocked
                    time.sleep(wait)
                else:
                    # Couldn't create the lock for some other reason
                    raise LockFailed
            else:
                open(self.unique_name, "wb")
                return

    def release(self):
        if not self.is_locked():
            raise NotLocked
        elif not os.path.exists(self.unique_name):
            raise NotMyLock
        os.unlink(self.unique_name)
        os.rmdir(self.lock_file)

    def is_locked(self):
        return os.path.exists(self.lock_file)

    def i_am_locking(self):
        return (self.is_locked() and
                os.path.exists(self.unique_name))

    def break_lock(self):
        if os.path.exists(self.lock_file):
            for name in os.listdir(self.lock_file):
                os.unlink(os.path.join(self.lock_file, name))
            os.rmdir(self.lock_file)

if hasattr(os, "link"):
    FileLock = LinkFileLock
else:
    FileLock = MkdirFileLock
FileLock = MkdirFileLock

def _after(dt, func, *args, **kwargs):
    """Execute func(*args, **kwargs) after dt seconds.

    Helper for docttests.
    """
    def _f():
        time.sleep(dt)
        func(*args, **kwargs)
    t = threading.Thread(target=_f)
    t.start()

def _testfile():
    """Return platform-appropriate lock file name.

    Helper for doctests.
    """
    import tempfile
    return os.path.join(tempfile.gettempdir(), 'trash-%s' % os.getpid())

def _lock_sleep_unlock():
    # Lock from another thread.
    lock = FileLock(_testfile())
    with lock:
        time.sleep(2.0)


if __name__ == "__main__":
    import doctest
    doctest.testmod()
