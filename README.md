# Kubernetes Platform Operator

A Kubernetes operator built in Python that automates deployment
lifecycle management for platform applications on AWS EKS.
Implements the operator pattern to continuously reconcile desired
state with actual cluster state, enabling reliable, high-availability
platform operations.

## Overview

This operator solves the challenge of managing complex deployment
lifecycles at scale automating the creation, updating, and health
monitoring of platform applications without manual intervention.
It integrates with Terraform for infrastructure provisioning,
Helm for packaging, Prometheus for monitoring, and GitHub Actions
for CI/CD.

## Features

- **Operator Pattern** - Continuous reconciliation loop ensures
  actual cluster state matches desired state
- **Deployment Lifecycle Management** - Automated create, update,
  and delete operations for platform applications
- **High-Availability** - Liveness and readiness probes with
  configurable replica management
- **Helm Packaging** - Production-ready Helm chart with RBAC,
  resource limits, and monitoring annotations
- **Terraform IaC** - AWS EKS cluster provisioning with IAM roles
  and node group management
- **Prometheus Monitoring** - Custom alerting rules for degraded
  apps, downtime, and reconcile errors
- **GitHub Actions CI/CD** - Automated testing, linting, Helm
  validation, and Docker build pipeline
- **Postmortem-Driven Reliability** - Structured error handling
  with status tracking for incident debugging

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Operator | Python, kubernetes-client |
| Packaging | Helm |
| Infrastructure | Terraform, AWS EKS |
| Monitoring | Prometheus, Grafana |
| CI/CD | GitHub Actions |
| Testing | PyTest |

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Run operator locally (requires kubeconfig)
cd operator
python main.py

# Deploy with Helm
helm install platform-operator helm/platform-operator/

# Provision EKS with Terraform
cd terraform
terraform init
terraform plan
terraform apply
```

## Architecture

```
┌─────────────────────────────────────────────┐
│         GitHub Actions CI/CD                 │
│  test → lint → helm-lint → build → deploy   │
├─────────────────────────────────────────────┤
│         Platform Operator (Python)           │
│  ┌──────────────────────────────────────┐   │
│  │    Reconciliation Loop (30s)          │   │
│  │  Desired State ──▶ Actual State       │   │
│  │  Create / Update / Delete / Health    │   │
│  └──────────────────────────────────────┘   │
├─────────────────────────────────────────────┤
│         AWS EKS Cluster (Terraform)          │
│  Node Group │ RBAC │ IAM Roles               │
├─────────────────────────────────────────────┤
│         Prometheus Monitoring                │
│  Degraded │ Down │ Reconcile Error Alerts    │
└─────────────────────────────────────────────┘
```

## Postmortem Process

When incidents occur:
1. Operator logs structured error with phase and error message
2. Prometheus alert fires within 2-5 minutes
3. On-call engineer reviews status conditions
4. Mitigation applied via reconcile loop or manual patch
5. Postmortem documents root cause and prevention
