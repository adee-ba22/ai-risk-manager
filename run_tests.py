import unittest
import sys
import test_app

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromModule(test_app)
    runner = unittest.TextTestRunner(stream=sys.stdout, verbosity=2)
    result = runner.run(suite)
    if not result.wasSuccessful():
        sys.exit(1)
