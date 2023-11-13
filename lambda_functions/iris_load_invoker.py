from lib import helper

def lambda_handler(event, context):
    
    print("##### Trigger Event #####")
    print(event)
    
    objectKey = event["Records"][0]["s3"]["object"]["key"]
    fileName = objectKey.split("/")[-1]
    helper.writeLog("info", "Load File:", fileName)

    if fileName == "swagger.json":
        helper.lambdaInvoker("iris_cache_loader", event)

    elif fileName in ("station.csv", "train.csv", "route.csv"):
        helper.lambdaInvoker("iris_cache_loader", event)
        helper.lambdaInvoker("iris_db_loader", event)

    return "Load Invoked!"
