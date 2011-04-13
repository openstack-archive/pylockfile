# -*- coding: utf-8 -*-
#
# tests/test_pidlockfile.py
#
# Copyright © 2008–2009 Ben Finney <ben+python@benfinney.id.au>
#
# This is free software: you may copy, modify, and/or distribute this work
# under the terms of the Python Software Foundation License, version 2 or
# later as published by the Python Software Foundation.
# No warranty expressed or implied. See the file LICENSE.PSF-2 for details.

""" Unit test for pidlockfile module.
"""

import __builtin__
import os
from StringIO import StringIO
import itertools
import tempfile
import errno

import scaffold

from lockfile import pidlockfile


def setup_pidlockfile_fixtures(testcase):
    """ Set up common fixtures for PIDLockFile test cases. """

    setup_pidfile_fixtures(testcase)

    testcase.pidlockfile_args = dict(
        path=testcase.scenario['path'],
        )

    testcase.test_instance = pidlockfile.PIDLockFile(
        **testcase.pidlockfile_args)

    scaffold.mock(
        "pidlockfile.write_pid_to_pidfile",
        tracker=testcase.mock_tracker)
    scaffold.mock(
        "pidlockfile.remove_existing_pidfile",
        tracker=testcase.mock_tracker)


class PIDLockFile_TestCase(scaffold.TestCase):
    """ Test cases for PIDLockFile class. """

    def setUp(self):
        """ Set up test fixtures. """
        setup_pidlockfile_fixtures(self)

    def tearDown(self):
        """ Tear down test fixtures. """
        scaffold.mock_restore()

    def test_instantiate(self):
        """ New instance of PIDLockFile should be created. """
        instance = self.test_instance
        self.failUnlessIsInstance(instance, pidlockfile.PIDLockFile)

    def test_has_specified_path(self):
        """ Should have specified path. """
        instance = self.test_instance
        expect_path = self.scenario['path']
        self.failUnlessEqual(expect_path, instance.path)


class PIDLockFile_read_pid_TestCase(scaffold.TestCase):
    """ Test cases for PIDLockFile.read_pid method. """

    def setUp(self):
        """ Set up test fixtures. """
        setup_pidlockfile_fixtures(self)
        self.scenario = self.scenarios['exist-currentpid']

    def tearDown(self):
        """ Tear down test fixtures. """
        os.unlink(self.test_instance.path)

    def test_gets_pid_via_read_pid_from_pidfile(self):
        """ Should get PID via read_pid_from_pidfile. """
        instance = self.test_instance
        self.scenario = self.scenarios['exist-otherpid']
        expect_pid = self.scenario['pidfile_pid']
        result = instance.read_pid()
        self.failUnlessEqual(expect_pid, result)


class PIDLockFile_is_locked_TestCase(scaffold.TestCase):
    """ Test cases for PIDLockFile.is_locked function. """

    def setUp(self):
        """ Set up test fixtures. """
        setup_pidlockfile_fixtures(self)
        self.scenario = self.scenarios['exist-currentpid']

    def tearDown(self):
        """ Tear down test fixtures. """
        scaffold.mock_restore()

        """ Should return True if PID file exists. """
        instance = self.test_instance
        expect_result = True
        self.scenario = self.scenarios['exist-currentpid']
        result = instance.is_locked()
        self.failUnlessEqual(expect_result, result)

    def test_returns_false_if_no_pid_file(self):
        """ Should return False if PID file does not exist. """
        instance = self.test_instance
        expect_result = False
        self.scenario = self.scenarios['nonexist']
        result = instance.is_locked()
        self.failUnlessEqual(expect_result, result)


class PIDLockFile_i_am_locking_TestCase(scaffold.TestCase):
    """ Test cases for PIDLockFile.i_am_locking function. """

    def setUp(self):
        """ Set up test fixtures. """
        setup_pidlockfile_fixtures(self)
        self.scenario = self.scenarios['exist-currentpid']

    def tearDown(self):
        """ Tear down test fixtures. """
        scaffold.mock_restore()

    def test_returns_false_if_no_pid_file(self):
        """ Should return False if PID file does not exist. """
        instance = self.test_instance
        expect_result = False
        self.scenario = self.scenarios['nonexist']
        result = instance.i_am_locking()
        self.failUnlessEqual(expect_result, result)

    def test_returns_false_if_pid_file_contains_bogus_pid(self):
        """ Should return False if PID file contains a bogus PID. """
        instance = self.test_instance
        expect_result = False
        self.scenario['pidfile'].write("bogus\n")
        result = instance.i_am_locking()
        self.failUnlessEqual(expect_result, result)

    def test_returns_false_if_pid_file_contains_different_pid(self):
        """ Should return False if PID file contains a different PID. """
        instance = self.test_instance
        expect_result = False
        self.scenario['pidfile'].write("0\n")
        result = instance.i_am_locking()
        self.failUnlessEqual(expect_result, result)

    def test_returns_true_if_pid_file_contains_current_pid(self):
        """ Should return True if PID file contains the current PID. """
        instance = self.test_instance
        expect_result = True
        result = instance.i_am_locking()
        self.failUnlessEqual(expect_result, result)


class PIDLockFile_acquire_TestCase(scaffold.TestCase):
    """ Test cases for PIDLockFile.acquire function. """

    def setUp(self):
        """ Set up test fixtures. """
        setup_pidlockfile_fixtures(self)
        self.scenario = self.scenarios['nonexist']

    def tearDown(self):
        """ Tear down test fixtures. """
        scaffold.mock_restore()

##    def test_raises_already_locked_if_file_exists(self):
##        """ Should raise AlreadyLocked error if PID file exists. """
##        instance = self.test_instance
##        self.scenario = self.scenarios['exist-currentpid']
##        test_error = OSError(
##            errno.EEXIST, "Already exists", self.scenario['path'])
##        pidlockfile.write_pid_to_pidfile.mock_raises = test_error
##        expect_error = pidlockfile.AlreadyLocked
##        self.failUnlessRaises(
##            expect_error,
##            instance.acquire)

    def test_writes_pid_to_specified_file(self):
        """ Should request writing current PID to specified file. """
        instance = self.test_instance
        pidfile_path = self.scenario['path']
        expect_mock_output = """\
            ...
            Called pidlockfile.write_pid_to_pidfile(%(pidfile_path)r)
            """ % vars()
        instance.acquire()
        scaffold.mock_restore()
        self.failUnlessMockCheckerMatch(expect_mock_output)

    def test_raises_lock_failed_on_write_error(self):
        """ Should raise LockFailed error if write fails. """
        instance = self.test_instance
        pidfile_path = self.scenario['path']
        mock_error = OSError(errno.EBUSY, "Bad stuff", pidfile_path)
        pidlockfile.write_pid_to_pidfile.mock_raises = mock_error
        expect_error = pidlockfile.LockFailed
        self.failUnlessRaises(
            expect_error,
            instance.acquire)


class PIDLockFile_release_TestCase(scaffold.TestCase):
    """ Test cases for PIDLockFile.release function. """

    def setUp(self):
        """ Set up test fixtures. """
        setup_pidlockfile_fixtures(self)
        self.scenario = self.scenarios['exist-currentpid']

    def tearDown(self):
        """ Tear down test fixtures. """
        scaffold.mock_restore()

    def test_raises_not_locked_if_no_pid_file(self):
        """ Should raise NotLocked error if PID file does not exist. """
        instance = self.test_instance
        self.scenario = self.scenarios['nonexist']
        expect_error = pidlockfile.NotLocked
        self.failUnlessRaises(
            expect_error,
            instance.release)

    def test_raises_not_my_lock_if_pid_file_not_locked_by_this_lock(self):
        """ Should raise NotMyLock error if PID file not locked by me. """
        instance = self.test_instance
        self.scenario = self.scenarios['exist-otherpid']
        expect_error = pidlockfile.NotMyLock
        self.failUnlessRaises(
            expect_error,
            instance.release)

    def test_removes_existing_pidfile(self):
        """ Should request removal of specified PID file. """
        instance = self.test_instance
        pidfile_path = self.scenario['path']
        expect_mock_output = """\
            ...
            Called pidlockfile.remove_existing_pidfile(%(pidfile_path)r)
            """ % vars()
        instance.release()
        scaffold.mock_restore()
        self.failUnlessMockCheckerMatch(expect_mock_output)


class PIDLockFile_break_lock_TestCase(scaffold.TestCase):
    """ Test cases for PIDLockFile.break_lock function. """

    def setUp(self):
        """ Set up test fixtures. """
        setup_pidlockfile_fixtures(self)
        self.scenario = self.scenarios['exist-otherpid']

    def tearDown(self):
        """ Tear down test fixtures. """
        scaffold.mock_restore()

    def test_returns_none_if_no_pid_file(self):
        """ Should return None if PID file does not exist. """
        instance = self.test_instance
        self.scenario = self.scenarios['nonexist']
        expect_result = None
        result = instance.break_lock()
        self.failUnlessEqual(expect_result, result)

    def test_removes_existing_pidfile(self):
        """ Should request removal of specified PID file. """
        instance = self.test_instance
        pidfile_path = self.scenario['path']
        expect_mock_output = """\
            ...
            Called pidlockfile.remove_existing_pidfile(%(pidfile_path)r)
            """ % vars()
        instance.break_lock()
        scaffold.mock_restore()
        self.failUnlessMockCheckerMatch(expect_mock_output)


class FakeFileDescriptorStringIO(StringIO, object):
    """ A StringIO class that fakes a file descriptor. """

    _fileno_generator = itertools.count()

    def __init__(self, *args, **kwargs):
        self._fileno = self._fileno_generator.next()
        super_instance = super(FakeFileDescriptorStringIO, self)
        super_instance.__init__(*args, **kwargs)

    def fileno(self):
        return self._fileno


def setup_pidfile_fixtures(testcase):
    """ Set up common fixtures for PID file test cases. """
    testcase.mock_tracker = scaffold.MockTracker()

    mock_current_pid = 235
    mock_other_pid = 8642
    mock_pidfile_current = FakeFileDescriptorStringIO(
        "%(mock_current_pid)d\n" % vars())
    mock_pidfile_other = FakeFileDescriptorStringIO(
        "%(mock_other_pid)d\n" % vars())
    mock_pidfile_path = tempfile.mktemp()

    scaffold.mock(
        "os.getpid",
        returns=mock_current_pid,
        tracker=testcase.mock_tracker)

    def mock_pidfile_open_nonexist(filename, mode, buffering):
        if 'r' in mode:
            raise IOError("No such file %(filename)r" % vars())
        else:
            result = testcase.scenario['pidfile']
        return result

    def mock_pidfile_open_exist(filename, mode, buffering):
        result = testcase.scenario['pidfile']
        return result

    def mock_open(filename, mode='r', buffering=None):
        if filename == testcase.scenario['path']:
            result = testcase.scenario['open_func'](
                filename, mode, buffering)
        else:
            result = FakeFileDescriptorStringIO()
        return result

    scaffold.mock(
        "__builtin__.open",
        returns_func=mock_open,
        tracker=testcase.mock_tracker)

    def mock_pidfile_os_open_nonexist(filename, flags, mode):
        if (flags & os.O_CREAT):
            result = testcase.scenario['pidfile'].fileno()
        else:
            raise OSError(errno.ENOENT, "No such file", filename)
        return result

    def mock_pidfile_os_open_exist(filename, flags, mode):
        result = testcase.scenario['pidfile'].fileno()
        return result

    def mock_os_open(filename, flags, mode=None):
        if filename == testcase.scenario['path']:
            result = testcase.scenario['os_open_func'](
                filename, flags, mode)
        else:
            result = FakeFileDescriptorStringIO().fileno()
        return result

    scaffold.mock(
        "os.open",
        returns_func=mock_os_open,
        tracker=testcase.mock_tracker)

    def mock_os_fdopen(fd, mode='r', buffering=None):
        if fd == testcase.scenario['pidfile'].fileno():
            result = testcase.scenario['pidfile']
        else:
            raise OSError(errno.EBADF, "Bad file descriptor")
        return result

    scaffold.mock(
        "os.fdopen",
        returns_func=mock_os_fdopen,
        tracker=testcase.mock_tracker)

    def mock_os_path_exists(path):
        if path == testcase.scenario['path']:
            result = testcase.scenario['path_exists_func']()
        else:
            result = False
        return result

    scaffold.mock(
        "os.path.exists",
        mock_obj=mock_os_path_exists)

    testcase.scenarios = {
        'nonexist': {
            'path': mock_pidfile_path,
            'pidfile': None,
            'pidfile_pid': None,
            'path_exists_func': (lambda: False),
            'os_open_func': mock_pidfile_os_open_nonexist,
            'open_func': mock_pidfile_open_nonexist,
            },
        'exist-currentpid': {
            'path': mock_pidfile_path,
            'pidfile': mock_pidfile_current,
            'pidfile_pid': mock_current_pid,
            'path_exists_func': (lambda: True),
            'os_open_func': mock_pidfile_os_open_exist,
            'open_func': mock_pidfile_open_exist,
            },
        'exist-otherpid': {
            'path': mock_pidfile_path,
            'pidfile': mock_pidfile_other,
            'pidfile_pid': mock_other_pid,
            'path_exists_func': (lambda: True),
            'os_open_func': mock_pidfile_os_open_exist,
            'open_func': mock_pidfile_open_exist,
            },
        }

    testcase.scenario = testcase.scenarios['nonexist']


class pidfile_exists_TestCase(scaffold.TestCase):
    """ Test cases for pidfile_exists function. """

    def setUp(self):
        """ Set up test fixtures. """
        setup_pidfile_fixtures(self)

    def tearDown(self):
        """ Tear down test fixtures. """
        scaffold.mock_restore()

    def test_returns_true_when_pidfile_exists(self):
        """ Should return True when pidfile exists. """
        self.scenario = self.scenarios['exist-otherpid']
        result = pidlockfile.pidfile_exists(self.scenario['path'])
        self.failUnless(result)

    def test_returns_false_when_no_pidfile_exists(self):
        """ Should return False when pidfile does not exist. """
        self.scenario = self.scenarios['nonexist']
        result = pidlockfile.pidfile_exists(self.scenario['path'])
        self.failIf(result)


class read_pid_from_pidfile_TestCase(scaffold.TestCase):
    """ Test cases for read_pid_from_pidfile function. """

    def setUp(self):
        """ Set up test fixtures. """
        setup_pidfile_fixtures(self)
        self.scenario = self.scenarios['exist-otherpid']

    def tearDown(self):
        """ Tear down test fixtures. """
        scaffold.mock_restore()

    def test_opens_specified_filename(self):
        """ Should attempt to open specified pidfile filename. """
        pidfile_path = self.scenario['path']
        expect_mock_output = """\
            Called __builtin__.open(%(pidfile_path)r, 'r')
            """ % vars()
        dummy = pidlockfile.read_pid_from_pidfile(pidfile_path)
        scaffold.mock_restore()
        self.failUnlessMockCheckerMatch(expect_mock_output)

    def test_reads_pid_from_file(self):
        """ Should read the PID from the specified file. """
        pidfile_path = self.scenario['path']
        expect_pid = self.scenario['pidfile_pid']
        pid = pidlockfile.read_pid_from_pidfile(pidfile_path)
        scaffold.mock_restore()
        self.failUnlessEqual(expect_pid, pid)

    def test_returns_pid_given_valid_input(self):
        """ Should return the PID if valid input file content. """
        pidfile_path = self.scenario['path']
        expect_pid = self.scenario['pidfile_pid']
        valid_inputs = [
            template % vars()
            for template in [
                "%(expect_pid)d\n",
                "%(expect_pid)09d\n",
                "%(expect_pid)d",
                "  %(expect_pid)09d  \n",
                "%(expect_pid)d\t",
                "%(expect_pid)d\n\n",
                "%(expect_pid)d\nFOO\n",
                ]
            ]
        for input_text in valid_inputs:
            self.scenario['pidfile'] = FakeFileDescriptorStringIO(input_text)
            pid = pidlockfile.read_pid_from_pidfile(pidfile_path)
            self.failUnlessEqual(
                expect_pid, pid,
                msg=(
                    "Input file content %(input_text)r"
                    " should give PID result %(expect_pid)r"
                    " (instead got %(pid)r)"
                    % vars()))

    def test_returns_none_given_invalid_input(self):
        """ Should return None if invalid input file content. """
        pidfile_path = self.scenario['path']
        invalid_inputs = [
            "",
            "\n",
            "B0GUS\n",
            "0x42\n",
            "  1e17  \n",
            ]
        for input_text in invalid_inputs:
            self.scenario['pidfile'] = FakeFileDescriptorStringIO(input_text)
            pid = pidlockfile.read_pid_from_pidfile(pidfile_path)
            self.failUnlessEqual(
                None, pid,
                msg=(
                    "Input file content %(input_text)r"
                    " should return None (instead got %(pid)r)"
                    % vars()))

    def test_returns_none_when_file_nonexist(self):
        """ Should return None when the PID file does not exist. """
        pidfile_path = self.scenario['path']
        self.scenario = self.scenarios['nonexist']
        pid = pidlockfile.read_pid_from_pidfile(pidfile_path)
        scaffold.mock_restore()
        self.failUnlessIs(None, pid)


class remove_existing_pidfile_TestCase(scaffold.TestCase):
    """ Test cases for remove_existing_pidfile function. """

    def setUp(self):
        """ Set up test fixtures. """
        setup_pidfile_fixtures(self)
        self.scenario = self.scenarios['exist-currentpid']

        scaffold.mock(
            "os.remove",
            tracker=self.mock_tracker)

    def tearDown(self):
        """ Tear down test fixtures. """
        scaffold.mock_restore()

    def test_removes_specified_filename(self):
        """ Should attempt to remove specified PID file filename. """
        pidfile_path = self.scenario['path']
        expect_mock_output = """\
            Called os.remove(%(pidfile_path)r)
            """ % vars()
        pidlockfile.remove_existing_pidfile(pidfile_path)
        scaffold.mock_restore()
        self.failUnlessMockCheckerMatch(expect_mock_output)

    def test_ignores_file_not_exist_error(self):
        """ Should ignore error if file does not exist. """
        pidfile_path = self.scenario['path']
        mock_error = OSError(errno.ENOENT, "Not there", pidfile_path)
        os.remove.mock_raises = mock_error
        expect_mock_output = """\
            Called os.remove(%(pidfile_path)r)
            """ % vars()
        pidlockfile.remove_existing_pidfile(pidfile_path)
        scaffold.mock_restore()
        self.failUnlessMockCheckerMatch(expect_mock_output)

    def test_propagates_arbitrary_oserror(self):
        """ Should propagate any OSError other than ENOENT. """
        pidfile_path = self.scenario['path']
        mock_error = OSError(errno.EACCES, "Denied", pidfile_path)
        os.remove.mock_raises = mock_error
        self.failUnlessRaises(
            mock_error.__class__,
            pidlockfile.remove_existing_pidfile,
            pidfile_path)


class write_pid_to_pidfile_TestCase(scaffold.TestCase):
    """ Test cases for write_pid_to_pidfile function. """

    def setUp(self):
        """ Set up test fixtures. """
        setup_pidfile_fixtures(self)
        self.scenario = self.scenarios['exist-currentpid']

    def tearDown(self):
        """ Tear down test fixtures. """
        scaffold.mock_restore()

    def test_opens_specified_filename(self):
        """ Should attempt to open specified PID file filename. """
        pidfile_path = self.scenario['path']
        expect_flags = (os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        expect_mode = 0x644
        expect_mock_output = """\
            Called os.open(%(pidfile_path)r, %(expect_flags)r, %(expect_mode)r)
            ...
            """ % vars()
        pidlockfile.write_pid_to_pidfile(pidfile_path)
        scaffold.mock_restore()
        self.failUnlessMockCheckerMatch(expect_mock_output)

    def test_writes_pid_to_file(self):
        """ Should write the current PID to the specified file. """
        pidfile_path = self.scenario['path']
        pidfile = self.scenario['pidfile']
        pidfile_pid = self.scenario['pidfile_pid']
        pidfile.close = scaffold.Mock(
            "mock_pidfile.close",
            tracker=self.mock_tracker)
        expect_line = "%(pidfile_pid)d\n" % vars()
        pidlockfile.write_pid_to_pidfile(pidfile_path)
        scaffold.mock_restore()
        self.failUnlessEqual(expect_line, pidfile.getvalue())

    def test_closes_file_after_write(self):
        """ Should close the specified file after writing. """
        pidfile_path = self.scenario['path']
        pidfile = self.scenario['pidfile']
        pidfile.write = scaffold.Mock(
            "mock_pidfile.write",
            tracker=self.mock_tracker)
        pidfile.close = scaffold.Mock(
            "mock_pidfile.close",
            tracker=self.mock_tracker)
        expect_mock_output = """\
            ...
            Called mock_pidfile.write(...)
            Called mock_pidfile.close()
            """ % vars()
        pidlockfile.write_pid_to_pidfile(pidfile_path)
        scaffold.mock_restore()
        self.failUnlessMockCheckerMatch(expect_mock_output)
