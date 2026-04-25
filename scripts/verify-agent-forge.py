#!/usr/bin/env python3
import sys

import omni_factory


if __name__ == "__main__":
    sys.argv = [sys.argv[0], "verify", *sys.argv[1:]]
    sys.exit(omni_factory.main())
