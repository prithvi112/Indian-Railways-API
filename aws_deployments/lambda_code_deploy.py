import sys
import os
import time
from zipfile import ZipFile
import boto3

rootFolder = os.path.dirname(os.path.abspath(__file__)) + '/'

##### Get folder and function name #####
scripts = sys.argv[1].split(',')
handlerScript = scripts[0]
funcName = sys.argv[2]
if len(sys.argv) == 4:
    libs = sys.argv[3].split(',')
else:
    libs = None

print('INFO    | Lambda handler script: ' + handlerScript)
print('INFO    | Files to be zipped: ' + str(scripts))

for i in range(1,len(scripts)):
    scripts[i] = './' + scripts[i]

##### Connect to Lambda client #####
lambda_client = boto3.client(
    'lambda',
    region_name=os.environ["aws_region"]    
)

##### Zip the py script #####
try:    
    with ZipFile('code.zip', 'w') as zip:
        for script in scripts:
            zip.write(script)
    print('SUCCESS | Lambda code has been zipped')
except Exception as e:
    print('ERROR   | Could not zip files')
    raise Exception(e)

with open('code.zip', 'rb') as file:
    zippedCode = file.read()

##### Change handler name and upload zipped code #####
lambdaHandler = handlerScript.split('.')[0] + '.lambda_handler'
print('INFO    | Lambda handler name: ' + lambdaHandler)
if libs:
    libArn = []
    print('INFO    | Lambda layers: ' + str(libs))
    layers = lambda_client.list_layers()
    for lib in libs:
        for layer in layers['Layers']:
            if layer['LayerName'] == lib:
                libArn.append(layer['LatestMatchingVersion']['LayerVersionArn'])
    print('INFO    | Lambda layer ARNs: ' + str(libArn))

    try:
        lambda_client.update_function_configuration(
            FunctionName=funcName,
            Handler=lambdaHandler,
            Layers=libArn
        )
        time.sleep(5)
        print('SUCCESS | Lambda configuration has been updated')
    except Exception as e:
        print('ERROR   | Could not update lambda configuration - ' + str(e))
        raise Exception('Could not update lambda configuration - ' + str(e))
else:
    try:
        lambda_client.update_function_configuration(
            FunctionName=funcName,
            Handler=lambdaHandler
        )
        time.sleep(5)
        print('SUCCESS | Lambda configuration has been updated')
    except Exception as e:
        print('ERROR   | Could not update lambda configuration - ' + str(e))
        raise Exception('Could not update lambda configuration - ' + str(e))

try:
    lambda_client.update_function_code(
        FunctionName=funcName,
        ZipFile=zippedCode
    )

    print('SUCCESS | Lambda code has been updated')
except Exception as e:
    print('ERROR   | Could not update lambda code - ' + str(e))
    raise Exception('Error in updating lambda code - ' + str(e))
