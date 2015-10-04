import unittest
import sys
import os.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

__author__ = 'Hao Lin'

if __name__ == "__main__":
    all_tests = unittest.TestLoader().discover('../test', pattern='*.py')
    unittest.TextTestRunner().run(all_tests)
