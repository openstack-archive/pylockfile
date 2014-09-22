# Copyright 2011 OpenStack Foundation.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from __future__ import absolute_import

import errno
import logging
import os
import threading
import time

LOG = logging.getLogger(__name__)

from . import _SharedBase


def _ensure_tree(path):
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise


class _FileLock(_SharedBase):
    """Lock implementation which allows multiple locks, working around
    issues like bugs.debian.org/cgi-bin/bugreport.cgi?bug=632857 and does
    not require any cleanup. Since the lock is always held on a file
    descriptor rather than outside of the process, the lock gets dropped
    automatically if the process crashes, even if __exit__ is not executed.

    There are no guarantees regarding usage by multiple green (or not green)
    threads in a single process here. This lock works only between
    processes. Exclusive access between local threads should be achieved using
    local in-process locks (which can be used in combination with this lock
    abstraction to acquire inter-process and intra-process locking).

    Note these locks are released when the descriptor is closed, so it's not
    safe to close the file descriptor while another green thread holds the
    lock. Just opening and closing the lock file can break synchronisation,
    so lock files must be accessed only using this abstraction.
    """

    def __init__(self, path):
        super(_SharedBase, self).__init__(path)
        self.lockfile = None

    def acquire(self):
        basedir = os.path.dirname(self.path)
        if not os.path.exists(basedir):
            _ensure_tree(basedir)
            LOG.info('Created lock path: %s', basedir)

        # Open in append mode so we don't overwrite any potential contents of
        # the target file.  This eliminates the possibility of an attacker
        # creating a symlink to an important file in our lock_path.
        self.lockfile = open(self.path, 'a')

        while True:
            try:
                # Using non-blocking locks since green threads are not
                # patched to deal with blocking locking calls.
                # Also upon reading the MSDN docs for locking(), it seems
                # to have a laughable 10 attempts "blocking" mechanism.
                self.trylock()
                LOG.debug('Got file lock "%s"', self.path)
                return True
            except IOError as e:
                if e.errno in (errno.EACCES, errno.EAGAIN):
                    # external locks synchronise things like iptables
                    # updates - give it some time to prevent busy spinning
                    time.sleep(0.01)
                else:
                    raise threading.ThreadError(_("Unable to acquire lock on"
                                                  " `%(filename)s` due to"
                                                  " %(exception)s") %
                                                {
                                                    'filename': self.path,
                                                    'exception': e,
                                                })

    def __enter__(self):
        self.acquire()
        return self

    def release(self):
        try:
            LOG.debug('Releasing file lock "%s"', self.path)
            self.unlock()
        except IOError:
            LOG.exception(_LE("Could not unlock the acquired lock `%s`"),
                          self.path)
        else:
            try:
                self.lockfile.close()
            except IOError:
                LOG.exception("Could not close the acquired file handle `%s`",
                              self.path)
            else:
                LOG.debug('Released and closed file lock associated with'
                          ' "%s"', self.path)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()

    def exists(self):
        return os.path.exists(self.path)

    def trylock(self):
        raise NotImplementedError()

    def unlock(self):
        raise NotImplementedError()


class _WindowsLock(_FileLock):
    def trylock(self):
        msvcrt.locking(self.lockfile.fileno(), msvcrt.LK_NBLCK, 1)

    def unlock(self):
        msvcrt.locking(self.lockfile.fileno(), msvcrt.LK_UNLCK, 1)


class _FcntlLock(_FileLock):
    def trylock(self):
        fcntl.lockf(self.lockfile, fcntl.LOCK_EX | fcntl.LOCK_NB)

    def unlock(self):
        fcntl.lockf(self.lockfile, fcntl.LOCK_UN)


if os.name == 'nt':
    import msvcrt
    AutoLockFile = _WindowsLock
else:
    import fcntl
    AutoLockFile = _FcntlLock
