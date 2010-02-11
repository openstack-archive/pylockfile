
"""
lockfile.py - Platform-independent advisory file locks.

Requires Python 2.5 unless you apply 2.4.diff
Locking is done on a per-thread basis instead of a per-process basis.

Usage:

>>> lock = FileLock('somefile')
>>> try:
...     lock.acquire()
... except AlreadyLocked:
...     print 'somefile', 'is locked already.'
... except LockFailed:
...     print 'somefile', 'can\\'t be locked.'
... else:
...     print 'got lock'
got lock
>>> print lock.is_locked()
True
>>> lock.release()

>>> lock = FileLock('somefile')
>>> print lock.is_locked()
False
>>> with lock:
...    print lock.is_locked()
True
>>> print lock.is_locked()
False

>>> lock = FileLock('somefile')
>>> # It is okay to lock twice from the same thread...
>>> with lock:
...     lock.acquire()
...
>>> # Though no counter is kept, so you can't unlock multiple times...
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
"""

from __future__ import division

import sys
import socket
import os
import threading
import time
import urllib
import warnings

# Work with PEP8 and non-PEP8 versions of threading module.
if not hasattr(threading, "current_thread"):
    threading.current_thread = threading.currentThread
if not hasattr(threading.Thread, "get_name"):
    threading.Thread.get_name = threading.Thread.getName

__all__ = ['Error', 'LockError', 'LockTimeout', 'AlreadyLocked',
           'LockFailed', 'UnlockError', 'NotLocked', 'NotMyLock',
           'LinkFileLock', 'MkdirFileLock', 'SQLiteFileLock',
           'LockBase']

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

class LockBase:
    """Base class for platform-specific lock classes."""
    def __init__(self, path, threaded=True):
        """
        >>> lock = LockBase('somefile')
        >>> lock = LockBase('somefile', threaded=False)
        """
        self.path = path
        self.lock_file = os.path.abspath(path) + ".lock"
        self.hostname = socket.gethostname()
        self.pid = os.getpid()
        if threaded:
            self.tname = "%x-" % (threading.current_thread().ident &
                                  0xffffffff)
        else:
            self.tname = ""
        dirname = os.path.dirname(self.lock_file)
        self.unique_name = os.path.join(dirname,
                                        "%s.%s%s" % (self.hostname,
                                                     self.tname,
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
        """
        raise NotImplemented("implement in subclass")

    def release(self):
        """
        Release the lock.

        If the file is not locked, raise NotLocked.
        """
        raise NotImplemented("implement in subclass")

    def is_locked(self):
        """
        Tell whether or not the file is locked.
        """
        raise NotImplemented("implement in subclass")

    def i_am_locking(self):
        """
        Return True if this object is locking the file.
        """
        raise NotImplemented("implement in subclass")

    def break_lock(self):
        """
        Remove a lock.  Useful if a locking thread failed to unlock.
        """
        raise NotImplemented("implement in subclass")

    def __enter__(self):
        """
        Context manager support.
        """
        self.acquire()
        return self

    def __exit__(self, *_exc):
        """
        Context manager support.
        """
        self.release()

def _fl_helper(cls, *args, **kwds):
    warnings.warn("Import LinkFileLock from lockfile.linkfilelock",
                  DeprecationWarning, stacklevel=2)
    # This is a bit funky, but it's only for awhile.  The way the unit tests
    # are constructed this function winds up as an unbound method, so it
    # actually takes three args, not two.  We want to toss out self.
    if not isinstance(args[0], str):
        # We are testing, avoid the first arg
        args = args[1:]
    if len(args) == 1 and not kwds:
        kwds["threaded"] = True
    return cls(*args, **kwds)

def LinkFileLock(*args, **kwds):
    """Factory function provided for backwards compatibility.

    Do not use in new code.  Instead, import LinkFileLock from the
    lockfile.linkfilelock module.
    """
    import linkfilelock
    return _fl_helper(linkfilelock.LinkFileLock, *args, **kwds)

def MkdirFileLock(*args, **kwds):
    """Factory function provided for backwards compatibility.

    Do not use in new code.  Instead, import MkdirFileLock from the
    lockfile.mkdirfilelock module.
    """
    import mkdirfilelock
    return _fl_helper(mkdirfilelock.MkdirFileLock, *args, **kwds)

def SQLiteFileLock(*args, **kwds):
    """Factory function provided for backwards compatibility.

    Do not use in new code.  Instead, import MkdirFileLock from the
    lockfile.mkdirfilelock module.
    """
    import sqlitefilelock
    return _fl_helper(sqlitefilelock.SQLiteFileLock, *args, **kwds)

if hasattr(os, "link"):
    import linkfilelock as _lfl
    FileLock = _lfl.LinkFileLock
else:
    import mkdirfilelock as _mfl
    FileLock = _mfl.MkdirFileLock
