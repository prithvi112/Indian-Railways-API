variable "aws_account_id" {
    type = string
}

variable "aws_region_name" {
    type = string
}

variable "lambda_name" {
    type = list
    default = ["iris_db_loader", "iris_api_handler", "iris_cache_loader", "iris_api_authorizer", "iris_load_invoker", "iris_search_loader"]
}

variable "lambda_description" {
    type = map
    default = {
        "iris_db_loader" = "Load data into RDS database from S3 source files",
        "iris_api_handler" = "Handle requests from IRIS API",
        "iris_cache_loader" = "Load data into Redis cache",
        "iris_api_authorizer" = "Handle API request authorization",
        "iris_load_invoker" = "Invoker for cache and database loaders",
        "iris_search_loader" = "Load data into OpenSearch cluster"
    }
}

variable "rds_db_name" {
    type = string
}

variable "rds_db_hostname" {
    type = string
}

variable "rds_db_username" {
    type = string
}

variable "rds_db_password" {
    type = string
}

variable "api_id" {
    type = string
}

variable "swagger_bucket_name" {
    type = string
}

variable "redis_cache_hostname" {
    type = string
}

variable "redis_cache_password" {
    type = string
}

variable "api_auth_key" {
    type = string
}

variable "search_hostname" {
    type = string
}

variable "search_username" {
    type = string
}

variable "search_password" {
    type = string
}