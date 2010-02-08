import sys

import lockfile

if sys.version_info >= (2, 5, 0):
    from _testhelper25 import ComplianceTest
else:
    from _testhelper23 import ComplianceTest
    
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
