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

import json
import os
import sys
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lambda"))

import pytest


@pytest.fixture(autouse=True)
def setup_env_vars():
    os.environ["LOCAL_DEV"] = "true"
    os.environ["DB_NAME"] = os.getenv("DB_NAME", "test_db")
    os.environ["DB_HOST"] = os.getenv("DB_HOST", "localhost")
    os.environ["DB_PORT"] = os.getenv("DB_PORT", "5432")
    os.environ["DB_USER"] = os.getenv("DB_USER", "test_user")
    os.environ["DB_PASSWORD"] = os.getenv("DB_PASSWORD", "test_password")
    os.environ["RDS_SCHEMA_BOA_APP_RDS_DATA"] = os.getenv(
        "RDS_SCHEMA_BOA_APP_RDS_DATA",
        "boa_app_rds_data",
    )
    os.environ["HANDLER_VERSION"] = "direct-v1"
    for k in (
        "NOTES_DELTA_TABLE",
        "NOTES_NIGHTLY_TABLE",
        "TOPICS_DELTA_TABLE",
        "TOPICS_NIGHTLY_TABLE",
        "FTS_DELTA_TABLE",
        "FTS_NIGHTLY_TABLE",
    ):
        os.environ.pop(k, None)


@pytest.fixture
def mock_context():
    context = Mock()
    context.aws_request_id = "test-request-id"
    return context


@pytest.fixture
def mock_secrets_manager():
    creds = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "username": os.getenv("DB_USER", "test_user"),
        "password": os.getenv("DB_PASSWORD", "test_password"),
    }
    with patch("db.secrets_client") as mock_secrets:
        mock_secrets.get_secret_value.return_value = {"SecretString": json.dumps(creds)}
        yield mock_secrets


@pytest.fixture
def note_upsert_event():
    return {
        "Records": [
            {
                "messageId": "test-message-1",
                "body": json.dumps(
                    {
                        "table": "notes",
                        "operation": "create",
                        "row": {
                            "id": 12345,
                            "sid": "SID001",
                            "body": "Student discussed graduation plan",
                            "author_uid": "uid123",
                            "author_name": "Jane Advisor",
                            "subject": "Lorem ipsum meeting notes",
                            "created_at": "2024-01-01T00:00:00Z",
                            "updated_at": "2024-01-01T00:00:00Z",
                        },
                    },
                ),
            },
        ],
    }


@pytest.fixture
def note_delete_event():
    return {
        "Records": [
            {
                "messageId": "test-message-2",
                "body": json.dumps(
                    {
                        "table": "notes",
                        "operation": "delete",
                        "row": {
                            "id": 99999,
                            "sid": "SID001",
                            "deleted_at": "2024-01-02T00:00:00Z",
                        },
                    },
                ),
            },
        ],
    }
