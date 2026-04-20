import pytest
from unittest.mock import MagicMock, patch
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'operator'))
from models import PlatformAppSpec, PlatformAppStatus, DeploymentPhase


@pytest.fixture
def sample_spec():
    return PlatformAppSpec(
        name="test-app",
        image="nginx:1.25",
        replicas=2,
        namespace="default",
        port=80,
        env_vars={"ENV": "test"},
        resource_limits={"cpu": "500m", "memory": "256Mi"}
    )


def test_platform_app_spec_defaults():
    spec = PlatformAppSpec(name="my-app", image="nginx:latest")
    assert spec.replicas == 2
    assert spec.namespace == "default"
    assert spec.port == 8080
    assert spec.health_check_path == "/health"


def test_platform_app_status_defaults():
    status = PlatformAppStatus()
    assert status.phase == DeploymentPhase.PENDING
    assert status.available_replicas == 0
    assert status.is_healthy() is False


def test_status_healthy():
    status = PlatformAppStatus(
        phase=DeploymentPhase.RUNNING,
        available_replicas=2,
        desired_replicas=2
    )
    assert status.is_healthy() is True


def test_status_degraded():
    status = PlatformAppStatus(
        phase=DeploymentPhase.RUNNING,
        available_replicas=1,
        desired_replicas=2
    )
    assert status.is_healthy() is False


def test_spec_labels(sample_spec):
    assert sample_spec.name == "test-app"
    assert sample_spec.replicas == 2
    assert sample_spec.env_vars["ENV"] == "test"


def test_deployment_phase_values():
    assert DeploymentPhase.RUNNING.value == "Running"
    assert DeploymentPhase.FAILED.value == "Failed"
    assert DeploymentPhase.SUCCEEDED.value == "Succeeded"


@patch("controller.config")
@patch("controller.client")
def test_controller_init(mock_client, mock_config):
    from controller import PlatformAppController
    mock_config.load_kube_config = MagicMock()
    mock_client.AppsV1Api = MagicMock()
    mock_client.CoreV1Api = MagicMock()
    controller = PlatformAppController(in_cluster=False)
    assert controller is not None