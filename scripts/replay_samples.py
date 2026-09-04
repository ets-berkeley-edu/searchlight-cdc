#!/usr/bin/env python3

"""
Copyright ©2026. The Regents of the University of California (Regents). All Rights Reserved.

Permission to use, copy, modify, and distribute this software and its documentation
for educational, research, and not-for-profit purposes, without fee and without a
signed licensing agreement, is hereby granted, provided that the above copyright
notice, this paragraph and the following two paragraphs appear in all copies,
modifications, and distributions.

Contact The Office of Technology Licensing, UC Berkeley, 2150 Shattuck Avenue,
Suite 510, Berkeley, CA 94720-1620, (510) 643-7201, otl@berkeley.edu,
http://ipira.berkeley.edu/industry-info for commercial licensing opportunities.

IN NO EVENT SHALL REGENTS BE LIABLE TO ANY PARTY FOR DIRECT, INDIRECT, SPECIAL,
INCIDENTAL, OR CONSEQUENTIAL DAMAGES, INCLUDING LOST PROFITS, ARISING OUT OF
THE USE OF THIS SOFTWARE AND ITS DOCUMENTATION, EVEN IF REGENTS HAS BEEN ADVISED
OF THE POSSIBILITY OF SUCH DAMAGE.

REGENTS SPECIFICALLY DISCLAIMS ANY WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE. THE
SOFTWARE AND ACCOMPANYING DOCUMENTATION, IF ANY, PROVIDED HEREUNDER IS PROVIDED
"AS IS". REGENTS HAS NO OBLIGATION TO PROVIDE MAINTENANCE, SUPPORT, UPDATES,
ENHANCEMENTS, OR MODIFICATIONS.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
import uuid
from pathlib import Path

"""Replay saved SAM-style CDC envelopes through handler.lambda_handler (local DB).

Usage:
  python scripts/replay_samples.py --dir events/examples
  python scripts/replay_samples.py --dir data/sqs_live --max 20
"""

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'lambda'))


def apply_env(fe: dict) -> None:
    os.environ['LOCAL_DEV'] = str(fe.get('LOCAL_DEV', 'true')).lower()
    for k in (
        'DB_HOST',
        'DB_PORT',
        'DB_USER',
        'DB_PASSWORD',
        'DB_NAME',
        'RDS_SCHEMA_BOA_APP_RDS_DATA',
        'HANDLER_VERSION',
    ):
        if k in fe:
            os.environ[k] = str(fe[k])
    os.environ.setdefault('RDS_SCHEMA_BOA_APP_RDS_DATA', 'boa_app_rds_data')


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        '--dir',
        default='events/examples',
        help='Directory of *.json envelopes',
    )
    ap.add_argument('--env-file', default='env.json')
    ap.add_argument('--max', type=int, default=0, help='Max files (0 = all)')
    args = ap.parse_args()

    env_path = ROOT / args.env_file
    if not env_path.exists():
        env_path = ROOT / 'env.json.example'
    fe = json.loads(env_path.read_text()).get('CDCHandler', {}) if env_path.exists() else {}
    apply_env(fe)

    handler = importlib.import_module('handler')
    importlib.reload(handler)

    class Ctx:
        aws_request_id = f'replay-{uuid.uuid4().hex[:12]}'

    files = sorted(Path(args.dir).glob('*.json'))
    if args.max:
        files = files[: args.max]
    ok = fail = 0
    for path in files:
        ev = json.loads(path.read_text())
        if 'Records' not in ev:
            print(f'SKIP {path.name}: not an envelope')  # noqa: T201
            continue
        resp = handler.lambda_handler(ev, Ctx())
        failures = resp.get('batchItemFailures') or []
        if failures:
            fail += 1
            print(f'FAIL {path.name} {failures}')  # noqa: T201
        else:
            ok += 1
            print(f'OK   {path.name}')  # noqa: T201
    print(f'Done: ok={ok} fail={fail}')  # noqa: T201
    return 1 if fail else 0


if __name__ == '__main__':
    raise SystemExit(main())
