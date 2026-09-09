# Deployment

Deploy lambda function code and dependencies to the AWS Cloud.

TODO: Which method to use for deploying to dev, qa, prod?
- Terraform (ops-managed)
- SAM CLI

Leveraging [Terraform + SAM integration](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/gs-terraform-support.html) would require terraform files in the local dev environment. We prefer to keep terraform files in a separate private repo.

## First-time setup

```bash
cp .env.example .env.dev   # never commit .env.dev
```
Override the variables with ARNs of existing resources. These will be passed to `sam deploy` to avoid re-creating them. Assign empty string if a resource doesn't exist.

## Build and package Python dependencies for deployment

Production dependencies are provided to the handler via lambda layers.
- boto3
- psycopg2

Other packages listed in requirements.txt are needed for local linting and testing only.

### Build lambda layers using AWS SAM CLI

Build an individual layer and output the .zip file to .aws-sam/build/

```bash
make build-Psycopg2Layer
```

Build the entire application including lambda function and layers configured the SAM template.
```bash
make build
```

### Build and deploy lambda layers using Docker and AWS CLI

#### Package dependencies in lambda layers

https://docs.aws.amazon.com/lambda/latest/dg/packaging-layers.html

Install a specific version of psycopg2 inside a docker container and output the .zip file to ./layers/

```bash
arch -x86_64 scripts/create_layer.sh psycopg2-python313 psycopg2-binary==2.9.10
```

#### Upload a layer to AWS Lambda

https://docs.aws.amazon.com/lambda/latest/dg/creating-deleting-layers.html

```bash
aws lambda publish-layer-version \
    --layer-name psycopg2-python313 \
    --zip-file ./layers/psycopg2-python313.zip \
    --compatible-runtimes python3.13
```

#### Add the layer to the lambda function

https://docs.aws.amazon.com/lambda/latest/dg/adding-layers.html

```bash
# Obtain the LayerVersion ARN of each layer
aws lambda list-layers
```
```bash
aws lambda update-function-configuration \
    --function-name lambda_handler \
    --layers LayerVersionArn1 LayerVersionArn2 ...
```

## Deploy the lambda

Uses CodeDeploy for safe deployment, incrementally shifting incoming message triggers from the old version to the new one.

### Deploy lambda and layers using AWS SAM CLI

Packages lambda function code in a .zip file and uploads it to an S3 bucket (aws-sam-cli-managed-default-*). Generates a CloudFormation changeset preview requiring confirmation to deploy.

```bash
# requires iam:PassRole permission
make deploy-dev
```

### Deploy lambda function code only

Updates code without necessarily requiring a CloudFormation deployment.

```bash
# requires iam:PassRole permission
make sync-dev
```

### Deploy lambda using AWS CLI

Deploy a local .zip file
```bash
aws lambda update-function-code \
    --function-name lambda_handler \
    --zip-file CDCHandler.zip
```

Deploy from S3
```bash
S3_BUCKET=$(aws cloudformation describe-stack-resources \
        --stack-name searchlight-cdc-dev \
        --query "StackResources[?ResourceType=='AWS::S3::Bucket'].PhysicalResourceId" \
        --output text)
aws lambda update-function-code \
    --function-name lambda_handler \
    --s3-bucket $(S3_BUCKET) \
    --s3-key searchlight-cdc-dev/<key>
```

### Test deployed changes

```bash
make test-remote
```
