import logging
import time
from datetime import datetime, timezone
from typing import Optional
from kubernetes import client, config
from kubernetes.client.exceptions import ApiException
from models import PlatformAppSpec, PlatformAppStatus, DeploymentPhase

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("platform-operator")


class PlatformAppController:
    """
    Kubernetes operator controller that automates deployment
    lifecycle management for PlatformApp custom resources.
    Reconciles desired state with actual cluster state.
    """

    def __init__(self, in_cluster: bool = False):
        if in_cluster:
            config.load_incluster_config()
        else:
            config.load_kube_config()
        self.apps_v1 = client.AppsV1Api()
        self.core_v1 = client.CoreV1Api()
        logger.info("PlatformAppController initialized")

    def reconcile(self, spec: PlatformAppSpec) -> PlatformAppStatus:
        """
        Main reconciliation loop — ensures actual state matches
        desired state for a given PlatformApp spec.
        """
        logger.info(f"Reconciling PlatformApp: {spec.name}")
        status = PlatformAppStatus(
            desired_replicas=spec.replicas,
            last_updated=datetime.now(timezone.utc).isoformat()
        )
        try:
            existing = self._get_deployment(spec.name, spec.namespace)
            if existing:
                logger.info(f"Updating deployment: {spec.name}")
                self._update_deployment(spec)
                status.conditions.append("DeploymentUpdated")
            else:
                logger.info(f"Creating deployment: {spec.name}")
                self._create_deployment(spec)
                self._create_service(spec)
                status.conditions.append("DeploymentCreated")
                status.conditions.append("ServiceCreated")

            # Wait for rollout and check health
            time.sleep(2)
            health = self._check_health(spec.name, spec.namespace)
            status.available_replicas = health.get("available", 0)
            status.phase = (
                DeploymentPhase.RUNNING
                if status.available_replicas > 0
                else DeploymentPhase.PENDING
            )
            logger.info(
                f"Reconcile complete: {spec.name} "
                f"phase={status.phase.value} "
                f"available={status.available_replicas}/"
                f"{status.desired_replicas}"
            )
        except ApiException as e:
            logger.error(f"Kubernetes API error: {e}")
            status.phase = DeploymentPhase.FAILED
            status.error_message = str(e)
        except Exception as e:
            logger.error(f"Reconcile error: {e}")
            status.phase = DeploymentPhase.FAILED
            status.error_message = str(e)
        return status

    def _get_deployment(
        self, name: str, namespace: str
    ) -> Optional[client.V1Deployment]:
        try:
            return self.apps_v1.read_namespaced_deployment(
                name=name, namespace=namespace)
        except ApiException as e:
            if e.status == 404:
                return None
            raise

    def _create_deployment(self, spec: PlatformAppSpec):
        deployment = client.V1Deployment(
            metadata=client.V1ObjectMeta(
                name=spec.name,
                namespace=spec.namespace,
                labels={**spec.labels, "app": spec.name,
                        "managed-by": "platform-operator"}
            ),
            spec=client.V1DeploymentSpec(
                replicas=spec.replicas,
                selector=client.V1LabelSelector(
                    match_labels={"app": spec.name}
                ),
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(
                        labels={"app": spec.name}
                    ),
                    spec=client.V1PodSpec(
                        containers=[
                            client.V1Container(
                                name=spec.name,
                                image=spec.image,
                                ports=[client.V1ContainerPort(
                                    container_port=spec.port)],
                                env=[
                                    client.V1EnvVar(name=k, value=v)
                                    for k, v in spec.env_vars.items()
                                ],
                                resources=client.V1ResourceRequirements(
                                    limits=spec.resource_limits,
                                    requests={
                                        "cpu": "100m",
                                        "memory": "128Mi"
                                    }
                                ),
                                liveness_probe=client.V1Probe(
                                    http_get=client.V1HTTPGetAction(
                                        path=spec.health_check_path,
                                        port=spec.port
                                    ),
                                    initial_delay_seconds=10,
                                    period_seconds=30
                                ),
                                readiness_probe=client.V1Probe(
                                    http_get=client.V1HTTPGetAction(
                                        path=spec.health_check_path,
                                        port=spec.port
                                    ),
                                    initial_delay_seconds=5,
                                    period_seconds=10
                                )
                            )
                        ]
                    )
                )
            )
        )
        self.apps_v1.create_namespaced_deployment(
            namespace=spec.namespace, body=deployment)
        logger.info(f"Created deployment: {spec.name}")

    def _update_deployment(self, spec: PlatformAppSpec):
        patch = {
            "spec": {
                "replicas": spec.replicas,
                "template": {
                    "spec": {
                        "containers": [{
                            "name": spec.name,
                            "image": spec.image,
                            "resources": {
                                "limits": spec.resource_limits
                            }
                        }]
                    }
                }
            }
        }
        self.apps_v1.patch_namespaced_deployment(
            name=spec.name, namespace=spec.namespace, body=patch)
        logger.info(f"Updated deployment: {spec.name}")

    def _create_service(self, spec: PlatformAppSpec):
        service = client.V1Service(
            metadata=client.V1ObjectMeta(
                name=spec.name,
                namespace=spec.namespace,
                labels={"app": spec.name,
                        "managed-by": "platform-operator"}
            ),
            spec=client.V1ServiceSpec(
                selector={"app": spec.name},
                ports=[client.V1ServicePort(
                    port=80,
                    target_port=spec.port
                )],
                type="ClusterIP"
            )
        )
        self.core_v1.create_namespaced_service(
            namespace=spec.namespace, body=service)
        logger.info(f"Created service: {spec.name}")

    def _check_health(
        self, name: str, namespace: str
    ) -> dict:
        try:
            dep = self.apps_v1.read_namespaced_deployment(
                name=name, namespace=namespace)
            return {
                "available": dep.status.available_replicas or 0,
                "ready": dep.status.ready_replicas or 0,
                "updated": dep.status.updated_replicas or 0
            }
        except ApiException:
            return {"available": 0, "ready": 0, "updated": 0}

    def delete(self, name: str, namespace: str):
        """Delete a managed PlatformApp deployment and service."""
        try:
            self.apps_v1.delete_namespaced_deployment(
                name=name, namespace=namespace)
            logger.info(f"Deleted deployment: {name}")
        except ApiException as e:
            if e.status != 404:
                raise
        try:
            self.core_v1.delete_namespaced_service(
                name=name, namespace=namespace)
            logger.info(f"Deleted service: {name}")
        except ApiException as e:
            if e.status != 404:
                raise