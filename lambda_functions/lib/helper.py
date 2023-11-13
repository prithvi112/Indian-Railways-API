from datetime import date
import boto3
from pymysql import connect
import os
from redis import Redis
import json

### Write log in specific format
def writeLog(logType, message1, message2=""):
    
    currentTime = date.today().strftime("%d-%m-%Y")
    print("{} | {} | {}".format(currentTime, logType.upper(), str(message1) + " " + str(message2)))

### Connect to AWS service
def connectService(service):

    writeLog("Warning", "Connecting to AWS service:", service)
    try:
        client = boto3.client(service, region_name=os.getenv("AWS_REGION"))
        writeLog("Success", "Connected to AWS service:", service)
    except Exception as e:
        writeLog("Error", "Could not connect to AWS service:", service)
        raise Exception(e)
    
    return client

### Connect to Relational Database
def dbConnection(action="open", connector=None):

    if action == "open":

        try:
            writeLog("info", "Connecting to Database")
            connection = connect(
                host=os.getenv("database_hostname"),
                user=os.getenv("database_username"),
                password=os.getenv("database_password"),
                port=3306,
                database=os.getenv("database_name")
            )
            writeLog("success", "Connected to Database")
            return connection
        except Exception as e:
            writeLog("error", "Connection could not be established")
            raise Exception(e)
    
    elif action == "close":
        writeLog("warning", "Closing Connection")
        connector.close()
        writeLog("success", "Connection closed successfully")

    else:
        writeLog("error", "Invalid action specified:", action)
    
### Query a Relational Database
def dbQuery(connector, qry, recordList=[], commit=False, many=False):

    cursor = connector.cursor()
    try:
        writeLog("warning", "Executing Query:", qry)
        if many:
            cursor.executemany(qry, recordList)
        else:
            cursor.execute(qry, recordList)
        writeLog("success", f"Query execution completed successfully")
        if commit:
            connector.commit()
        writeLog("info", "Affected Rows:", cursor.rowcount)
        result = cursor.fetchall()
    except Exception as e:
        writeLog("error", "Could not execute query:", str(e))
    finally:
        cursor.close() 

    return result

### Download file from S3 bucket
def eventFileDownloader(bucket="", key="", trigger=False, triggerEvent={}):

    if trigger:
        writeLog("info", "Fetching bucket information from trigger event")
        bucketName = triggerEvent["Records"][0]["s3"]["bucket"]["name"]
        objectKey = triggerEvent["Records"][0]["s3"]["object"]["key"]
        
    else:
        writeLog("info", "Bucket information provided")
        bucketName = bucket
        objectKey = key

    fileName = objectKey.split("/")[-1]
    writeLog("Info", "Bucket Name:", bucketName)
    writeLog("Info", "Object Key:", objectKey)
    writeLog("Info", "File Name:", fileName)

    s3Client = connectService("s3")
    s3Client.download_file(
        Bucket=bucketName,
        Key=objectKey,
        Filename="/tmp/" + fileName
    )
    writeLog("success", "File Downloaded:", os.listdir("/tmp"))

    return fileName

### Connect to Redis cache
def cacheConnection():
    
    try:
        
        writeLog("warning", "Connecting to Cache")
        redisClient = Redis(
            host=os.getenv("cache_hostname"),
            port=6379,
            password=os.getenv("cache_password"),
            decode_responses=True
        )
        if redisClient.ping():
            writeLog("success", "Connected to Cache")
    except Exception as e:
        writeLog("error", "Connection could not be established")
        raise Exception(e)
    
    return redisClient

### Interacting with Redis cache
def cacheTransaction(redisClient, hashKey, action="load", recordKey="", hashMap={}, every=False):

    writeLog("info", "Redis Hash Key:", hashKey)
    writeLog("info", "Cache Transaction Action: ", action)

    if action == "load":
        initalRecords = len(hashMap.keys())
        writeLog("info", "Record Count:", str(initalRecords))
        writeLog("warning", "Loading data into cache")

        try:
            insertRows = redisClient.hset(
                hashKey,
                mapping=hashMap
            )
            writeLog("success", "Cache data load completed")
            writeLog("info", "Records Inserted:", insertRows)
            writeLog("info", "Records Updated:", initalRecords - insertRows)

        except Exception as e:
            writeLog("error", "Cache data load failed")
            raise Exception(e)
        result = None

    elif action == "fetch":

        try:
            if every:
                writeLog("warning", "Fetching all records")
                result = redisClient.hgetall(hashKey)
                writeLog("success", f"{len(result.keys())} records fetched")
                #return record
            
            else:
                if isinstance(recordKey, list):
                    writeLog("info", "Cache Record Keys:", recordKey)
                    result = redisClient.hmget(hashKey, recordKey)
                    if len(recordKey) == len(result):
                        writeLog("success", "Found all keys")
                    else:
                        writeLog("warning", f"All keys were not found")
                    writeLog("info", f"{len(result)} records fetched")
                else:
                    writeLog("info", "Cache Record Key:", recordKey)
                    writeLog("info", "Checking Key")
                    keyExist = redisClient.hexists(hashKey, recordKey)
                    if keyExist:
                        writeLog("success", "Given Key Found")
                        record = redisClient.hget(hashKey, recordKey)
                        result = json.loads(record)
                        writeLog("success", "Cache data fetch completed")
                    else:
                        writeLog("warning", "Given Key Not Found")
                        result = None

        except Exception as e:
            writeLog("error", "Cache data fetch failed")
            raise Exception(e)

    return result

### Invoke another lambda function
def lambdaInvoker(function, payload):

    lambdaClient = connectService("lambda")
    try:
        writeLog("warning", "Invoking lambda function:", function)

        lambdaClient.invoke(
            FunctionName=function,
            InvocationType="Event",
            Payload=json.dumps(payload)
        )
        writeLog("success", "Function invoked")
    except Exception as e:
        writeLog("error", "Function invocation failed:", str(e))


