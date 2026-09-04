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
import os
from pathlib import Path

import psycopg2

"""Apply sql/*.sql with schema placeholder substitution."""

SQL_DIR = Path(__file__).resolve().parents[1] / 'sql'
FILES = ('001_schema.sql', '002_tables.sql', '003_indexes.sql')


def main() -> int:
    ap = argparse.ArgumentParser(description='Apply direct schema SQL')
    ap.add_argument('--host', default=os.environ.get('DB_HOST', 'localhost'))
    ap.add_argument('--port', type=int, default=int(os.environ.get('DB_PORT', '5432')))
    ap.add_argument('--user', default=os.environ.get('DB_USER', 'test_user'))
    ap.add_argument('--password', default=os.environ.get('DB_PASSWORD', ''))
    ap.add_argument('--dbname', default=os.environ.get('DB_NAME', 'test_db'))
    ap.add_argument(
        '--schema',
        default=os.environ.get('RDS_SCHEMA_BOA_APP_RDS_DATA', 'boa_app_rds_data'),
    )
    args = ap.parse_args()

    subs = {
        '{rds_schema_boa_app_rds_data}': args.schema,
        '{rds_app_boa_user}': args.user,
    }
    conn = psycopg2.connect(
        host=args.host,
        port=args.port,
        user=args.user,
        password=args.password,
        dbname=args.dbname,
    )
    conn.autocommit = True
    with conn.cursor() as cur:
        for name in FILES:
            sql = (SQL_DIR / name).read_text()
            for k, v in subs.items():
                sql = sql.replace(k, v)
            print(f'Applying {name} ...')  # noqa: T201
            cur.execute(sql)
    conn.close()
    print(f'Schema {args.schema} ready.')  # noqa: T201
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
