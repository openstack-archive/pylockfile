.. warning::

   **This package is deprecated**. It is highly preferred that instead of
   using this code base, `fasteners`_ or `oslo.concurrency`_ is
   used.

The lockfile package exports a ``LockFile`` class which provides a simple API
for locking files.  Unlike the Windows ``msvcrt.locking`` function, the
``fcntl.lockf`` and ``fcntl.flock`` functions, and the deprecated ``posixfile
module``, the API is identical across both UNIX (including Linux and Mac) and
Windows platforms.

The lock mechanism relies on the atomic nature of the link (on UNIX) and
``mkdir`` (on Windows) system calls.  An implementation based on SQLite is also
provided, more as a demonstration of the possibilities it provides than as
production-quality code.

Install pylockfile with: ``pip install lockfile``.

* `Documentation <http://docs.openstack.org/developer/pylockfile>`_
* `Source <http://git.openstack.org/cgit/openstack/pylockfile>`_
* `Bugs <http://bugs.launchpad.net/pylockfile>`_

For any questions or comments or further help needed please email
`openstack-dev`_ and prefix your email subject with ``[oslo][pylockfile]`` (for
a faster response).

In version 0.9 the API changed in two significant ways:

* It changed from a module defining several classes to a package containing
  several modules, each defining a single class.

* Where classes had been named ``SomethingFileLock`` before the last two words
  have been reversed, so that class is now ``SomethingLockFile``.

The previous module-level definitions of ``LinkFileLock``, ``MkdirFileLock``
and ``SQLiteFileLock`` will be retained until the 1.0 release.

.. _fasteners: https://pypi.python.org/pypi/fasteners
.. _oslo.concurrency: http://docs.openstack.org/developer/oslo.concurrency/
.. _openstack-dev: http://lists.openstack.org/cgi-bin/mailman/listinfo/openstack-dev
