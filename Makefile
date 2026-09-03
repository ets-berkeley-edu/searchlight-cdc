include .env.dev
export

.PHONY: help build-Psycopg2Layer build-Boto3Layer build test-unit apply-sql sam-test sam-test-all consume-sqs consume-sqs-dry-run replay check deploy-dev test-remote publish

SAM_EVENTS := notes-create notes-update notes-delete note_topics-create note_topics-update note_topics-delete
SAM := LOCAL_DEV=true sam local invoke CDCHandler --env-vars env.json
PARAMS := --parameter-overrides LambdaRoleArn=$(LAMBDA_ROLE_ARN)

ifneq ($(BOTO3_LAYER_ARN), "")
	PARAMS += Boto3LayerArn=$(BOTO3_LAYER_ARN)
endif
ifneq ($(PSYCOPG2_LAYER_ARN), "")
	PARAMS += Psycopg2LayerArn=$(PSYCOPG2_LAYER_ARN)
endif

help:
	@echo "Direct-table CDC production pack"
	@echo "  make apply-sql           Apply sql/*.sql"
	@echo "  make test-unit           pytest test/unit/"
	@echo "  make sam-test            SAM invoke notes-create"
	@echo "  make sam-test-all        SAM invoke all 6 examples"
	@echo "  make replay              Replay events/examples through handler"
	@echo "  make consume-sqs         Live SQS → handler (never deletes messages)"
	@echo "  make consume-sqs-dry-run Queue access check only"

build-Psycopg2Layer:
ifeq ($(PSYCOPG2_LAYER_ARN), "")
	mkdir -p "$(ARTIFACTS_DIR)/python"
	python -m pip install --no-cache-dir --disable-pip-version-check psycopg2-binary==2.9.10 -t "$(ARTIFACTS_DIR)/python"
	cd $(ARTIFACTS_DIR) && zip -r psycopg2-python313.zip .
	rm -rf "$(ARTIFACTS_DIR)/python"
else
	@echo "Skipping psycopg2 layer build; given existing resource ARN"
endif

build-Boto3Layer:
ifeq ($(BOTO3_LAYER_ARN), "")
	mkdir -p "$(ARTIFACTS_DIR)/python"
	python -m pip install --no-cache-dir --disable-pip-version-check boto3 -t "$(ARTIFACTS_DIR)/python"
	cd $(ARTIFACTS_DIR) && zip -r boto3-python313.zip .
	rm -rf "$(ARTIFACTS_DIR)/python"
else
	@echo "Skipping boto3 layer build; given existing resource ARN"
endif

build:
	sam build $(PARAMS)

sam-test: build
	$(SAM) --event events/examples/notes-create.json

sam-test-all: build
	@for e in $(SAM_EVENTS); do echo "=== $$e ==="; $(SAM) --event events/examples/$$e.json || exit 1; done

replay:
	python scripts/replay_samples.py --dir events/examples

apply-sql:
	python scripts/apply_sql.py

test-unit:
	PYTHONPATH=lambda pytest test/unit/ -v

consume-sqs:
	python scripts/sqs_consume.py --env-key CDCHandler

consume-sqs-dry-run:
	python scripts/sqs_consume.py --env-key CDCHandler --dry-run --max-messages 5

check:
	ruff check lambda/ test/ scripts/ && ruff format --check lambda/ test/ scripts/

sync-dev:
	sam sync --config-env dev --resource AWS::Serverless::Function --stack-name searchlight-cdc-dev $(PARAMS)

deploy-dev: build
	sam deploy --config-env dev $(PARAMS)

test-remote:
	sam remote invoke CDCHandler --stack-name searchlight-cdc-dev --event-file events/examples/notes-create.json
