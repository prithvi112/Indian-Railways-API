# Indian Railways Information System (IRIS)

For viewing and interacting with the API, use the [IRIS Swagger UI](https://d3gtv471y7lib.cloudfront.net/iris-service-api/swagger.html)

### API Resource Checklist [10]

Base Path: /iris-service-api/v2/railways

- [x] /swagger 
- [x] /overview
- [x] /stations
- [x] /stations/codes
- [x] /trains
- [x] /trains/numbers
- [x] /trains/status
- [x] /route/all
- [x] /route/station
- [x] /route/availabilty

### Architecture Component

Cloud Environment - Amazon Web Services (AWS)

Services -  
* Identity and Access Management (IAM)
* Elastic Compute Cloud (EC2)  
* Simple Storage Service (S3)
* Lambda
* API Gateway
* Relational Database Service (RDS)
* CloudFront

Infrastructure Management - Terraform
