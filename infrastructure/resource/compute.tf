########## Amazon Lambda ##########


locals {
    lambda_env_variable = {
        "iris_db_loader" = {
            database_hostname = var.rds_db_hostname,
            database_username = var.rds_db_username,
            database_password = var.rds_db_password,
            database_name = var.rds_db_name
        },
        "iris_api_handler" = {
            database_hostname = var.rds_db_hostname,
            database_username = var.rds_db_username,
            database_password = var.rds_db_password,
            database_name = var.rds_db_name,
            swagger_bucket = var.swagger_bucket_name,
            cache_hostname = var.redis_cache_hostname,
            cache_password = var.redis_cache_password
        },
        "iris_cache_loader" = {
            cache_hostname = var.redis_cache_hostname,
            cache_password = var.redis_cache_password
        },
        "iris_api_authorizer" = {
            account_id = var.aws_account_id,
            api_id = var.api_id,
            api_key = var.api_auth_key
        },
        "iris_load_invoker" = {},
        "iris_search_loader" = {
            search_hostname = var.search_hostname,
            search_username = var.search_username,
            search_password = var.search_password,
            cache_hostname = var.redis_cache_hostname,
            cache_password = var.redis_cache_password
        }
    }
    lambda_layers = {
        "iris_db_loader" = [
            "arn:aws:lambda:${var.aws_region_name}:${var.aws_account_id}:layer:numpy:1",
            "arn:aws:lambda:${var.aws_region_name}:${var.aws_account_id}:layer:pandas:5",
            "arn:aws:lambda:${var.aws_region_name}:${var.aws_account_id}:layer:pymysql:2",
            "arn:aws:lambda:${var.aws_region_name}:${var.aws_account_id}:layer:redis:1",
            "arn:aws:lambda:${var.aws_region_name}:${var.aws_account_id}:layer:opensearch-py:1"
        ],
        "iris_api_handler" = [
            "arn:aws:lambda:${var.aws_region_name}:${var.aws_account_id}:layer:pymysql:2",
            "arn:aws:lambda:${var.aws_region_name}:${var.aws_account_id}:layer:redis:1",
            "arn:aws:lambda:${var.aws_region_name}:${var.aws_account_id}:layer:bs4:2",
            "arn:aws:lambda:${var.aws_region_name}:${var.aws_account_id}:layer:requests:2",
            "arn:aws:lambda:${var.aws_region_name}:${var.aws_account_id}:layer:opensearch-py:1"
        ],
        "iris_cache_loader" = [
            "arn:aws:lambda:${var.aws_region_name}:${var.aws_account_id}:layer:pymysql:2",
            "arn:aws:lambda:${var.aws_region_name}:${var.aws_account_id}:layer:redis:1",
            "arn:aws:lambda:${var.aws_region_name}:${var.aws_account_id}:layer:opensearch-py:1"
        ],
        "iris_api_authorizer" = [
            "arn:aws:lambda:${var.aws_region_name}:${var.aws_account_id}:layer:pymysql:2",
            "arn:aws:lambda:${var.aws_region_name}:${var.aws_account_id}:layer:redis:1",
            "arn:aws:lambda:${var.aws_region_name}:${var.aws_account_id}:layer:opensearch-py:1"
        ],
        "iris_load_invoker" = [
            "arn:aws:lambda:${var.aws_region_name}:${var.aws_account_id}:layer:pymysql:2",
            "arn:aws:lambda:${var.aws_region_name}:${var.aws_account_id}:layer:redis:1",
            "arn:aws:lambda:${var.aws_region_name}:${var.aws_account_id}:layer:opensearch-py:1"
        ],
        "iris_search_loader" = [
            "arn:aws:lambda:${var.aws_region_name}:${var.aws_account_id}:layer:pymysql:2",
            "arn:aws:lambda:${var.aws_region_name}:${var.aws_account_id}:layer:redis:1",
            "arn:aws:lambda:${var.aws_region_name}:${var.aws_account_id}:layer:opensearch-py:1"
        ]
    }
}


##### Function - 5
resource "aws_lambda_function" "lambdaFunction" {
    count = length(var.lambda_name)
    function_name = element(var.lambda_name,count.index)
    role = "arn:aws:iam::${var.aws_account_id}:role/lambda_service_role"
    handler = "${element(var.lambda_name,count.index)}.lambda_handler"
    runtime = "python3.10"
    timeout = 60
    filename = "../../lambda_functions/sample_lambda.zip"
    architectures = ["x86_64"]
    description = lookup(var.lambda_description, element(var.lambda_name,count.index))
    layers = lookup(local.lambda_layers, element(var.lambda_name,count.index))

    environment {
        variables = lookup(local.lambda_env_variable, element(var.lambda_name,count.index))
    }
}

##### Configure cloudwatch log group - 5
resource "aws_cloudwatch_log_group" "lambdaLogs" {
    count = length(var.lambda_name)
    name = "/aws/lambda/${aws_lambda_function.lambdaFunction[count.index].function_name}"
    retention_in_days = 3
}

##### S3 Invoke Permission - 2
resource "aws_lambda_permission" "s3InvokerLambdaPermission" {
    statement_id = "allow_s3_to_invoke_iris_load_invoker"
    action = "lambda:InvokeFunction"
    function_name = aws_lambda_function.lambdaFunction[4].arn
    principal = "s3.amazonaws.com"
    source_arn = aws_s3_bucket.s3Bucket.arn
}

resource "aws_lambda_permission" "s3InvokerLambdaSwaggerPermission" {
    statement_id = "allow_s3_to_invoke_iris_load_invoker_swagger"
    action = "lambda:InvokeFunction"
    function_name = aws_lambda_function.lambdaFunction[4].arn
    principal = "s3.amazonaws.com"
    source_arn = "arn:aws:s3:::${var.swagger_bucket_name}"
}

##### S3 Trigger - 2
resource "aws_s3_bucket_notification" "s3InvokerLambdaTrigger" {
    bucket = aws_s3_bucket.s3Bucket.id
    lambda_function {
        lambda_function_arn = aws_lambda_function.lambdaFunction[4].arn
        events = ["s3:ObjectCreated:*"]
        filter_prefix = "files/"
        filter_suffix = ".csv"
    }
}

resource "aws_s3_bucket_notification" "s3InvokerLambdaSwaggerTrigger" {
    bucket = var.swagger_bucket_name
    lambda_function {
        lambda_function_arn = aws_lambda_function.lambdaFunction[4].arn
        events = ["s3:ObjectCreated:*"]
        filter_prefix = "iris-service-api/swagger/"
        filter_suffix = ".json"
    }
}