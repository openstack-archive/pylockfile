import sys

import lockfile

from compliancetest import ComplianceTest
    
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
