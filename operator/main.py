import logging
import time
import signal
import sys
from controller import PlatformAppController
from models import PlatformAppSpec

logger = logging.getLogger("platform-operator")
running = True


def handle_signal(signum, frame):
    global running
    logger.info(f"Received signal {signum}, shutting down gracefully")
    running = False


signal.signal(signal.SIGTERM, handle_signal)
signal.signal(signal.SIGINT, handle_signal)


def load_sample_specs():
    """Sample PlatformApp specs for demonstration."""
    return [
        PlatformAppSpec(
            name="api-gateway",
            image="nginx:1.25",
            replicas=3,
            namespace="default",
            port=80,
            env_vars={"ENV": "production", "LOG_LEVEL": "info"},
            resource_limits={"cpu": "500m", "memory": "256Mi"},
            labels={"tier": "frontend"}
        ),
        PlatformAppSpec(
            name="backend-service",
            image="python:3.11-slim",
            replicas=2,
            namespace="default",
            port=8080,
            env_vars={"ENV": "production", "PORT": "8080"},
            resource_limits={"cpu": "1000m", "memory": "512Mi"},
            labels={"tier": "backend"}
        )
    ]


def run_operator():
    """Main operator reconciliation loop."""
    logger.info("Starting Kubernetes Platform Operator")
    controller = PlatformAppController(in_cluster=False)
    specs = load_sample_specs()
    reconcile_interval = 30  # seconds

    while running:
        logger.info(
            f"Running reconciliation for {len(specs)} PlatformApps")
        for spec in specs:
            status = controller.reconcile(spec)
            logger.info(
                f"  {spec.name}: phase={status.phase.value} "
                f"replicas={status.available_replicas}/"
                f"{status.desired_replicas} "
                f"healthy={status.is_healthy()}"
            )
        logger.info(
            f"Reconciliation complete. "
            f"Next run in {reconcile_interval}s"
        )
        time.sleep(reconcile_interval)

    logger.info("Operator shutdown complete")


if __name__ == "__main__":
    run_operator()