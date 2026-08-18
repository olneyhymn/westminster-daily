#!/usr/bin/env python3
"""
Mint short-lived AWS credentials scoped to one named task.

The standing key can do exactly one thing: assume the agent role. It holds no
S3 access of its own, so on its own it is close to worthless -- which is the
point. Real work runs under a credential that expires within the hour and is
narrowed, by a session policy, to the task that asked for it.

Session policies can only subtract. Whatever a task file asks for, the result
is the intersection of that file with the role's ceiling, so a task cannot
reach past the ceiling however it is written -- and the ceiling's explicit
denials (every delete, every bucket reconfiguration, all of IAM) survive
regardless.

The task name becomes the STS session name, so CloudTrail records which task
performed every call.

Usage:
    eval "$(uv run scripts/aws_session.py audio-upload)"
    uv run scripts/aws_session.py read-only --duration 900 --json
    uv run scripts/aws_session.py --list
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).parent.parent
TASKS = REPO / "ops" / "aws" / "tasks"
ROLE_ARN = "arn:aws:iam::212595366334:role/claude-agent"


def available():
    return sorted(p.stem for p in TASKS.glob("*.json"))


def assume(task, duration):
    policy = TASKS / f"{task}.json"
    if not policy.exists():
        sys.exit(f"No such task: {task}. Available: {', '.join(available())}")
    result = subprocess.run(
        [
            "aws", "sts", "assume-role",
            "--role-arn", ROLE_ARN,
            # Prefixed so a glance at CloudTrail says which task, run by what.
            "--role-session-name", f"claude-{task}",
            "--duration-seconds", str(duration),
            "--policy", f"file://{policy}",
            "--output", "json",
        ],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        sys.exit(f"assume-role failed:\n{result.stderr.strip()}")
    return json.loads(result.stdout)["Credentials"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task", nargs="?", help="name of a file in ops/aws/tasks")
    parser.add_argument("--duration", type=int, default=3600,
                        help="seconds until expiry (900-3600)")
    parser.add_argument("--json", action="store_true",
                        help="emit JSON instead of shell exports")
    parser.add_argument("--list", action="store_true", help="list available tasks")
    args = parser.parse_args()

    if args.list or not args.task:
        print("tasks:", ", ".join(available()))
        return

    creds = assume(args.task, args.duration)
    if args.json:
        print(json.dumps(creds, indent=2, default=str))
        return

    # Shell exports, so the caller can eval this straight into an environment.
    print(f"export AWS_ACCESS_KEY_ID={creds['AccessKeyId']}")
    print(f"export AWS_SECRET_ACCESS_KEY={creds['SecretAccessKey']}")
    print(f"export AWS_SESSION_TOKEN={creds['SessionToken']}")
    print(f"# scoped to '{args.task}', expires {creds['Expiration']}", file=sys.stderr)


if __name__ == "__main__":
    main()
