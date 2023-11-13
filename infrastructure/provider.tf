### Set AWS provider for Terraform

terraform {
    required_providers {
      aws = {
        source = "hashicorp/aws"
        version = "~> 4.0"
      }
    }
}

provider "aws" {
    default_tags {
        tags = {
            "managed_by" = "terraform",
            "aws_project_id" = "iris"
        }
    }
}

# Set S3 bucket for terraform state
terraform {
    backend "s3" {
        key = "iris_infra/iris.tfstate"
    }
}