# AWS Lambda Deployment Guide

This guide deploys the API and SQS workers to AWS Lambda as Docker container images, keeps Postgres on Supabase, uses DynamoDB/SQS for production state and jobs, runs the long RAWG catalog sync on ECS Fargate, and hosts the frontend on Cloudflare Pages.

## 1. Accounts, Tools, And Safety

Create or log into AWS, enable MFA on the root account, and create a monthly AWS Budget. Start with a USD 10 budget and alerts at 50%, 80%, and 100%.

Install:

```bash
aws --version
sam --version
docker --version
```

Configure AWS:

```bash
aws configure
```

Use one AWS region consistently. `ap-southeast-1` is a good default if you want Singapore-region AWS resources.

## 2. Supabase Postgres

Create a Supabase project and copy the pooled connection string. Use the pooler URL on port `6543`, and add `sslmode=require`.

Example shape:

```text
postgresql://postgres.project-ref:password@aws-0-region.pooler.supabase.com:6543/postgres?sslmode=require
```

Run migrations from your machine:

```bash
cd backend
source .venv/bin/activate
DATABASE_URL='postgresql://...' alembic upgrade head
```

Do not run migrations from Lambda cold starts.

## 3. Deploy API And Workers With SAM

Copy the example config and edit the values:

```bash
cp infrastructure/samconfig.toml.example infrastructure/samconfig.toml
```

At minimum, replace:

- `DatabaseUrl`
- `SecretKey`
- `AllowedOrigins`
- `CookieDomain`
- `RawgApiKey`
- optional `GeminiApiKey`, `AnthropicApiKey`, `GoogleClientId`

Deploy:

```bash
cd infrastructure
sam build --template-file template.yaml
sam deploy --guided --resolve-image-repos
```

SAM creates:

- API Gateway HTTP API
- FastAPI Lambda using `backend/Dockerfile.lambda`
- SQS queues and DLQs
- Lambda SQS workers using `backend/Dockerfile.lambda`
- DynamoDB TTL key/value table
- daily and weekly RAWG SQS schedules
- managed ECR repositories for the Lambda container images

After deploy, test the default API URL from the SAM output:

```bash
curl https://your-api-id.execute-api.ap-southeast-1.amazonaws.com/api/health
```

## 4. Fargate RAWG Catalog Sync

The API and SQS worker Lambdas already use the Lambda container image built by SAM. The long monthly RAWG sync uses a separate Fargate image from `backend/Dockerfile.rawg`.

Create an ECR repository:

```bash
aws ecr create-repository --repository-name video-game-recommender-rawg
```

Build and push the RAWG image:

```bash
cd backend
docker build -f Dockerfile.rawg -t video-game-recommender-rawg .
aws ecr get-login-password --region ap-southeast-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.ap-southeast-1.amazonaws.com
docker tag video-game-recommender-rawg:latest <account-id>.dkr.ecr.ap-southeast-1.amazonaws.com/video-game-recommender-rawg:latest
docker push <account-id>.dkr.ecr.ap-southeast-1.amazonaws.com/video-game-recommender-rawg:latest
```

In the AWS Console, create:

- an ECS cluster
- a Fargate task definition using the pushed image
- container name `rawg`
- public subnet networking
- `Assign public IP = ENABLED`
- a security group that allows outbound HTTPS

Set the same environment variables on the ECS task that the API uses, especially:

- `APP_ENV=production`
- `APP_RUNTIME=fargate`
- `KV_BACKEND=dynamodb`
- `TASK_BACKEND=sqs`
- `DATABASE_URL`
- `DYNAMODB_KV_TABLE`
- `RAWG_API_KEY`
- `RAWG_BASE_URL`

Redeploy SAM with these parameters filled:

- `EcsClusterArn`
- `EcsRawgTaskDefinitionArn`
- `EcsRawgContainerName`
- `EcsSubnetIds`
- `EcsSecurityGroupIds`
- `EcsTaskExecutionRoleArn`

Then enable the `MonthlyRawgCatalogRule` EventBridge rule, or trigger it manually from the admin endpoint.

Tiny smoke test command for the ECS task:

```bash
python -m app.jobs.rawg_job sync-catalog --max-requests 2
```

## 5. API Custom Domain

Use a real root domain so cookies work across frontend and API subdomains:

```text
https://app.yourdomain.com
https://api.yourdomain.com
COOKIE_DOMAIN=.yourdomain.com
```

In AWS Certificate Manager, request a certificate for `api.yourdomain.com`.

In API Gateway:

- create custom domain `api.yourdomain.com`
- attach the ACM certificate
- map the API stage to `/`

In DNS, point `api.yourdomain.com` to the API Gateway custom domain target.

Verify:

```bash
curl https://api.yourdomain.com/api/health
```

## 6. Cloudflare Pages Frontend

Connect the repo to Cloudflare Pages.

Settings:

- root directory: `frontend`
- build command: `npm run build`
- output directory: `dist`

Environment variable:

```text
VITE_API_URL=https://api.yourdomain.com/api
```

Add custom domain:

```text
app.yourdomain.com
```

The file `frontend/public/_redirects` makes React Router routes serve `index.html` on refresh.

## 7. Smoke Tests

API:

```bash
curl https://api.yourdomain.com/api/health
```

In the browser:

- register
- login
- refresh an authenticated page
- add a game to the library
- update and delete a library entry
- open recommendations
- trigger AI Picks if keys are configured
- check `/api/admin/pipeline/status` as an admin

Workers:

- add/update library entry and confirm recommendation precompute logs in CloudWatch
- trigger AI Picks and confirm the SQS worker changes status from pending to ready or failed
- run RAWG Fargate with `--max-requests 2`

## 8. Cost Controls

Keep Lambda outside a VPC. Do not add a NAT Gateway for this deployment.

Keep these guardrails:

- AWS Budget alert
- API Gateway throttling if traffic grows
- Lambda reserved concurrency
- RAWG request budget settings
- CloudWatch log retention, ideally 7-14 days
- SQS DLQ review after failures

The first likely cost jump is upgrading Supabase/Neon Postgres, not Lambda itself.
