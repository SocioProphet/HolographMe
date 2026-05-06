#!/usr/bin/env python3
from pathlib import Path
import sys

repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

from holographme.bundle import main

raise SystemExit(main())
