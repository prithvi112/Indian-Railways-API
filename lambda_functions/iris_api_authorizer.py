from lib import helper
import os

def lambda_handler(event, context):

    helper.writeLog("warning", "API Authorization Request")
    
    if event["authorizationToken"] == os.getenv("api_key"):
        auth = "Allow"
        helper.writeLog("success", "User authorized successfully")
    else:
        auth = "Deny"
        helper.writeLog("error", "Incorrect token provided")
    
    helper.writeLog("info", "API Authorization Response:", auth)
    accountId = os.getenv("account_id")
    apiId = os.getenv("api_id")
    accountRegion = os.getenv("AWS_REGION")
    authPolicy = {
                    "principalId": "auth_policy",
                    "policyDocument": {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Action": "execute-api:Invoke",
                            "Resource": [
                                f"arn:aws:execute-api:{accountRegion}:{accountId}:{apiId}/*/*"
                            ],
                            "Effect": auth
                        }
                    ]
                }
            }
    
    return authPolicy
