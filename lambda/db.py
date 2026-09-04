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

import json
import logging
import os
from typing import Any

import boto3
import psycopg2
from logging_utils import log, log_exception

"""Database connection helpers for CDC Lambda handlers.

Production: credentials from AWS Secrets Manager (DB_SECRET_NAME).
Local/SAM:  LOCAL_DEV=true reads DB_HOST, DB_USER, etc. from environment.
"""


DB_SECRET_NAME = os.environ.get("DB_SECRET_NAME", "")
DB_NAME = os.environ.get("DB_NAME", "")

_secrets_client = None
_db_credentials: dict[str, Any] | None = None
SERVICE_NAME = "advising-notes-search-cdc-db"


def _local_credentials() -> dict[str, Any]:
    """Build connection dict from env vars (local dev and pytest)."""
    try:
        from local_secrets import get_local_db_credentials

        return get_local_db_credentials()
    except ImportError:
        return {
            "host": os.environ.get("DB_HOST", "localhost"),
            "port": int(os.environ.get("DB_PORT", "5432")),
            "username": os.environ.get("DB_USER", "test_user"),
            "password": os.environ.get("DB_PASSWORD", "test_password"),
        }


def get_db_credentials() -> dict[str, Any]:
    """Retrieve and cache database credentials."""
    global _db_credentials
    if os.environ.get("LOCAL_DEV", "false").lower() == "true":
        log(SERVICE_NAME, logging.DEBUG, "Using local DB credentials from environment")
        return _local_credentials()
    if _db_credentials is None:
        log(
            SERVICE_NAME,
            logging.INFO,
            "Loading DB credentials from Secrets Manager",
            secret_name=DB_SECRET_NAME,
        )
        try:
            secret_response = get_secrets_client().get_secret_value(SecretId=DB_SECRET_NAME)
            _db_credentials = json.loads(secret_response["SecretString"])
        except Exception as e:
            log_exception(
                SERVICE_NAME,
                "Error getting DB credentials from Secrets Manager",
                e,
                secret_name=DB_SECRET_NAME,
            )
    return _db_credentials


def get_db_connection() -> psycopg2.extensions.connection:
    """Create a new PostgreSQL connection (one per Lambda invocation)."""
    creds = get_db_credentials()
    dbname = os.environ.get("DB_NAME", DB_NAME)
    log(
        SERVICE_NAME,
        logging.DEBUG,
        "Connecting to database",
        host=creds.get("host"),
        dbname=dbname,
    )
    return psycopg2.connect(
        host=creds["host"],
        port=creds.get("port", 5432),
        user=creds["username"],
        password=creds["password"],
        dbname=dbname,
        connect_timeout=5,
    )


def get_secrets_client():
    global _secrets_client
    if _secrets_client is None:
        _secrets_client = boto3.client("secretsmanager")
    return _secrets_client
