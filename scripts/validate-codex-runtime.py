#!/usr/bin/env python3
from __future__ import annotations

import sys

import omni_factory


if __name__ == "__main__":
    sys.argv = [sys.argv[0], "validate-codex-runtime", *sys.argv[1:]]
    raise SystemExit(omni_factory.main())
