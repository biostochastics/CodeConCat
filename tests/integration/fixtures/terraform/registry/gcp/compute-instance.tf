# GCP Compute Instance Module - Based on terraform-google-modules/vm/google
# https://registry.terraform.io/modules/terraform-google-modules/vm/google/latest

terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "The GCP zone"
  type        = string
  default     = "us-central1-a"
}

variable "instance_name" {
  description = "Name of the compute instance"
  type        = string
  default     = "my-instance"
}

variable "machine_type" {
  description = "Machine type"
  type        = string
  default     = "e2-medium"
}

variable "network" {
  description = "Network name"
  type        = string
  default     = "default"
}

variable "subnetwork" {
  description = "Subnetwork name"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Network tags"
  type        = list(string)
  default     = []
}

variable "labels" {
  description = "Labels to apply to the instance"
  type        = map(string)
  default = {
    environment = "production"
    managed_by  = "terraform"
  }
}

variable "startup_script" {
  description = "Startup script"
  type        = string
  default     = ""
}

variable "metadata" {
  description = "Instance metadata"
  type        = map(string)
  default     = {}
}

# Compute Instance
resource "google_compute_instance" "main" {
  name         = var.instance_name
  machine_type = var.machine_type
  zone         = var.zone

  tags   = var.tags
  labels = var.labels

  boot_disk {
    initialize_params {
      image = data.google_compute_image.debian.self_link
      size  = 20
      type  = "pd-standard"
    }
  }

  network_interface {
    network    = var.network
    subnetwork = var.subnetwork != "" ? var.subnetwork : null

    access_config {
      # Ephemeral public IP
    }
  }

  metadata = merge(
    var.metadata,
    {
      startup-script = var.startup_script
    }
  )

  service_account {
    email  = google_service_account.main.email
    scopes = ["cloud-platform"]
  }

  scheduling {
    preemptible       = false
    automatic_restart = true
  }

  allow_stopping_for_update = true
}

# Service Account
resource "google_service_account" "main" {
  account_id   = "${var.instance_name}-sa"
  display_name = "Service Account for ${var.instance_name}"
}

# IAM Roles
resource "google_project_iam_member" "instance_log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.main.email}"
}

resource "google_project_iam_member" "instance_metric_writer" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.main.email}"
}

# Firewall Rules
resource "google_compute_firewall" "allow_ssh" {
  name    = "${var.instance_name}-allow-ssh"
  network = var.network

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = var.tags
}

resource "google_compute_firewall" "allow_http" {
  name    = "${var.instance_name}-allow-http"
  network = var.network

  allow {
    protocol = "tcp"
    ports    = ["80", "443"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = var.tags
}

# Data Sources
data "google_compute_image" "debian" {
  family  = "debian-11"
  project = "debian-cloud"
}

data "google_compute_zones" "available" {
  region = var.region
  status = "UP"
}

# Outputs
output "instance_id" {
  description = "The server-assigned unique identifier of the instance"
  value       = google_compute_instance.main.instance_id
}

output "instance_self_link" {
  description = "The URI of the created resource"
  value       = google_compute_instance.main.self_link
}

output "instance_name" {
  description = "The name of the instance"
  value       = google_compute_instance.main.name
}

output "internal_ip" {
  description = "The internal IP address of the instance"
  value       = google_compute_instance.main.network_interface[0].network_ip
}

output "external_ip" {
  description = "The external IP address of the instance"
  value       = google_compute_instance.main.network_interface[0].access_config[0].nat_ip
}

output "service_account_email" {
  description = "The email of the service account"
  value       = google_service_account.main.email
}

locals {
  instance_labels = merge(
    var.labels,
    {
      name   = var.instance_name
      region = var.region
      zone   = var.zone
    }
  )
}
