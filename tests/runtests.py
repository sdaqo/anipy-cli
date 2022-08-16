import sys

sys.path.insert(0, ".")

import pytest

if __name__ == "__main__":
    args = sys.argv.copy()
    args.pop(0)
    pytest.main(args)
