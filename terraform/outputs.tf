output "cluster_name" {
  description = "EKS cluster name"
  value       = aws_eks_cluster.platform.name
}

output "cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = aws_eks_cluster.platform.endpoint
}

output "cluster_version" {
  description = "Kubernetes version"
  value       = aws_eks_cluster.platform.version
}