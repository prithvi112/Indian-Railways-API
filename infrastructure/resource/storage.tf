########## Amazon Simple Storage Service (S3) ##########

##### Bucket - 1
resource "aws_s3_bucket" "s3Bucket" {
    bucket = "iris-internal-bucket"
}
