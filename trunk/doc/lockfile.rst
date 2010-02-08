
:mod:`lockfile` --- Platform-independent file locking
=====================================================

.. module:: lockfile
   :synopsis: Platform-independent file locking
.. moduleauthor:: Skip Montanaro <skip@pobox.com>
.. sectionauthor:: Skip Montanaro <skip@pobox.com>


.. versionadded:: "not yet"

.. note::

   This module is very definitely alpha.  It is quite possible that the API
   and implementation will change in important ways as people test it and
   provide feedback and bug fixes.  In particular, if the mkdir-based
   locking scheme is sufficient for both Windows and Unix platforms, the
   link-based scheme may be deleted so that only a single locking scheme is
   used, providing cross-platform lockfile cooperation.

The :mod:`lockfile` module exports a :class:`FileLock` class which provides
a simple API for locking files.  Unlike the Windows :func:`msvcrt.locking`
function, the Unix :func:`fcntl.flock`, :func:`fcntl.lockf` and the
deprecated :mod:`posixfile` module, the API is identical across both Unix
(including Linux and Mac) and Windows platforms.  The lock mechanism relies
on the atomic nature of the :func:`link` (on Unix) and :func:`mkdir` (On
Windows) system calls.

.. note::

   The current implementation uses :func:`os.link` on Unix, but since that
   function is unavailable on Windows it uses :func:`os.mkdir` there.  At
   this point it's not clear that using the :func:`os.mkdir` method would be
   insufficient on Unix systems.  If it proves to be adequate on Unix then
   the implementation could be simplified and truly cross-platform locking
   would be possible.  (It's mostly possible now, but the :func:`break_lock`
   method needs some work.)

.. note::

   The current implementation doesn't provide for shared vs. exclusive
   locks.  It should be possible for multiple reader processes to lock a
   file at the same time.

The module defines the following exceptions:

.. exception:: Error

   This is the base class for all exceptions raised by the :class:`LockFile`
   class.

.. exception:: LockError

   This is the base class for all exceptions raised when attempting to lock
   a file.

.. exception:: UnlockError

   This is the base class for all exceptions raised when attempting to
   unlock a file.

.. exception:: LockTimeout

   This exception is raised if the :func:`LockFile.acquire` method is
   called with a timeout which expires before an existing lock is released.

.. exception:: AlreadyLocked

   This exception is raised if the :func:`LockFile.acquire` detects a
   file is already locked when in non-blocking mode.

.. exception:: LockFailed

   This exception is raised if the :func:`LockFile.acquire` detects some
   other condition (such as a non-writable directory) which prevents it from
   creating its lock file.

.. exception:: NotLocked

   This exception is raised if the file is not locked when
   :func:`LockFile.release` is called.

.. exception:: NotMyLock

   This exception is raised if the file is locked by another thread or
   process when :func:`LockFile.release` is called.

The following class is provided:


.. class:: FileLock(path, threaded=True)

   *path* is an object in the file system to be locked.  It need not exist,
   but its directory must exist and be writable at the time the
   :func:`acquire` and :func:`release` methods are called.
   *threaded* is optional, but when set to :const:`True` locks will be
   distinguished between threads in the same process.

.. note::

   ... Describe on-disk lock file structure here ...

.. seealso::

   Module :mod:`msvcrt`
      Provides the :func:`locking` function, the standard Windows way of
      locking (parts of) a file.

   Module :mod:`posixfile`
      The deprecated (since Python 1.5) way of locking files on Posix systems.

   Module :mod:`fcntl`
      Provides the current best way to lock files on Unix systems
      (:func:`lockf` and :func:`flock`.

Implementing Other Locking Schemes
----------------------------------

There is a :class:`_FileLock` base class which can be used as the foundation
for other locking schemes.  For example, if shared filesystems are not
available, :class:`_FileLock` could be subclassed to provide locking via an
SQL database.  There is an example SQLiteFileLock class which uses an SQLite
file database as the underlying lock mechanism.

FileLock Objects
----------------

:class:`FileLock` objects support the :term:`context manager` protocol used
by the statement:`with` statement.

:class:`FileLock` has the following user-visible methods:

.. method:: FileLock.acquire(timeout=None)

   Lock the file associated with the :class:`FileLock` object.  If the
   *timeout* is omitted or :const:`None` the caller will block until the
   file is unlocked by the object currently holding the lock.  If the
   *timeout* is zero or a negative number the :exc:`AlreadyLocked` exception
   will be raised if the file is currently locked by another process or
   thread.  If the *timeout* is positive, the caller will block for that
   many seconds waiting for the lock to be released.  If the lock is not
   released within that period the :exc:`LockTimeout` exception will be
   raised.

.. method:: FileLock.release()

   Unlock the file associated with the :class:`FileLock` object.  If the
   file is not currently locked, the :exc:`NotLocked` exception is raised.
   If the file is locked by another thread or process the :exc:`NotMyLock`
   exception is raised.

.. method:: is_locked()

   Return the status of the lock on the current file.  If any process or
   thread (including the current one) is locking the file, :const:`True` is
   returned, otherwise :const:`False` is returned.

.. method:: break_lock()

   If the file is currently locked, break it.

Examples
--------

This example is the "hello world" for the :mod:`lockfile` module::

    lock = FileLock("/some/file/or/other")
    with lock:
        print lock.path, 'is locked.'

To use this with versions of Python before 2.5, you can execute::

    lock = FileLock("/some/file/or/other")
    lock.acquire()
    print lock.path, 'is locked.'
    lock.release()

If you don't want to wait forever, you might try::	

    lock = FileLock("/some/file/or/other")
    while not lock.i_am_locking():
	try:
	    lock.acquire(timeout=60)    # wait up to 60 seconds
	except LockTimeout:
	    lock.break_lock()
	    lock.acquire()
    print "I locked", lock.path
    lock.release()
