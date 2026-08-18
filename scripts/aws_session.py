#!/usr/bin/env python3
"""
Deferred to the shared broker at ~/.local/bin/aws-session.

The broker outgrew this repo the moment a second project needed credentials,
so it lives in one place and reads task policies from both ~/.config/claude-aws/tasks
and this repo's ops/aws/tasks. This path stays because it is the one the skill
and the habit both point at.
"""

import os
import sys
from pathlib import Path

BROKER = Path.home() / ".local" / "bin" / "aws-session"

if not BROKER.exists():
    sys.exit(f"Shared broker missing: {BROKER}")
os.execv(sys.executable, [sys.executable, str(BROKER), *sys.argv[1:]])
