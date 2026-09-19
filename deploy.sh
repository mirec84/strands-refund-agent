#!/usr/bin/env bash
set -euo pipefail

export AWS_REGION="us-east-1"
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export REPO_NAME="strands-refund-agent"

# 1. Create ECR repository
aws ecr create-repository \
  --repository-name "$REPO_NAME" \
  --region "$AWS_REGION"

# 2. Authenticate Docker with ECR
aws ecr get-login-password --region "$AWS_REGION" | \
  docker login --username AWS --password-stdin \
  "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

# 3. Build container image for ARM64 architecture
docker buildx build --platform linux/arm64 \
  -t "$REPO_NAME:latest" .

# 4. Tag and push to ECR
docker tag "$REPO_NAME:latest" \
  "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$REPO_NAME:latest"
docker push \
  "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$REPO_NAME:latest"

# 5. Create the AgentCore execution role
aws iam create-role \
  --role-name AgentCoreRefundAgentRole \
  --assume-role-policy-document file://trust-policy.json

aws iam attach-role-policy \
  --role-name AgentCoreRefundAgentRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonBedrockFullAccess

# 6. Deploy to AgentCore Runtime
agentcore deploy \
  --name "strands-refund-agent" \
  --image-uri "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$REPO_NAME:latest" \
  --execution-role-arn "arn:aws:iam::$AWS_ACCOUNT_ID:role/AgentCoreRefundAgentRole" \
  --region "$AWS_REGION"

# 7. Smoke-test it
agentcore invoke \
  --name "strands-refund-agent" \
  --payload '{"prompt": "My order ORD-3003 arrived damaged, can I get a refund of $89 for it?"}'
