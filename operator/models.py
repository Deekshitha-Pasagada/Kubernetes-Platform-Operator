from dataclasses import dataclass, field
from typing import Optional, List, Dict
from enum import Enum


class DeploymentPhase(Enum):
    PENDING = "Pending"
    RUNNING = "Running"
    SUCCEEDED = "Succeeded"
    FAILED = "Failed"
    DEGRADED = "Degraded"


@dataclass
class PlatformAppSpec:
    """Spec for a PlatformApp custom resource."""
    name: str
    image: str
    replicas: int = 2
    namespace: str = "default"
    port: int = 8080
    env_vars: Dict[str, str] = field(default_factory=dict)
    resource_limits: Dict[str, str] = field(default_factory=lambda: {
        "cpu": "500m",
        "memory": "256Mi"
    })
    health_check_path: str = "/health"
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class PlatformAppStatus:
    """Status of a PlatformApp managed deployment."""
    phase: DeploymentPhase = DeploymentPhase.PENDING
    available_replicas: int = 0
    desired_replicas: int = 0
    conditions: List[str] = field(default_factory=list)
    last_updated: Optional[str] = None
    error_message: Optional[str] = None

    def is_healthy(self) -> bool:
        return (
            self.phase == DeploymentPhase.RUNNING
            and self.available_replicas == self.desired_replicas
        )