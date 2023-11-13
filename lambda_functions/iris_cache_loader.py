from lib import helper
import json
import csv
import os

def jsonGenerate(filename, redisClient):

    data = {}
    with open("/tmp/" + filename) as csvFile:
        rows = csv.DictReader(csvFile)

        if filename == "station.csv":
            for row in rows:
                data[row["stationCode"]] = json.dumps(
                    {
                        "stationCode": row["stationCode"],
                        "stationName": row["stationName"],
                        "stateName": row["stateName"],
                        "railwaysZoneShort": row["railwaysZone"],
                        "railwaysZoneFull": row["railwaysDivision"]
                    }
                )

            hashValue = "stations"

        elif filename == "train.csv":
            allStations = helper.cacheTransaction(
                    redisClient,
                    "stations",
                    "fetch",
                    every=True
                )
            
            for key in allStations.keys():
                allStations[key] = json.loads(allStations[key])

            for row in rows:
                row["trainNumber"] = row["trainNumber"].zfill(5)
                data[row["trainNumber"]] = json.dumps(
                    {
                        "trainNumber": row["trainNumber"],
                        "trainName": row["trainName"],
                        "sourceStationCode": row["sourceStation"],
                        "sourceStationName": allStations[row["sourceStation"]]["stationName"],
                        "destinationStationCode": row["destinationStation"],
                        "destinationStationName": allStations[row["destinationStation"]]["stationName"],
                        "trainType": row["trainType"],
                        "serviceDays": row["serviceDays"],
                        "coachClass": row["coachClass"],
                        "travelDuration": row["travelDuration"],
                        "travelDistance": row["travelDistance"],
                        "stopCount": row["stopCount"],
                        "averageSpeed": row["averageSpeed"]
                    }
                )
                
            hashValue = "trains"

        elif filename == "route.csv":
            allTrains = helper.cacheTransaction(
                redisClient,
                "trains",
                "fetch",
                every=True
            )

            allStations = helper.cacheTransaction(
                    redisClient,
                    "stations",
                    "fetch",
                    every=True
                )
            for key in allStations.keys():
                allStations[key] = json.loads(allStations[key])
            for key in allTrains.keys():
                allTrains[key] = json.loads(allTrains[key])
                
            stage = {}
            
            for row in rows:
                
                row["trainNumber"] = row["trainNumber"].zfill(5)
                trainNumber = row.pop("trainNumber")

                newRow = {
                    "stationCode": row["stationCode"],
                    "stationName": allStations[row["stationCode"]]["stationName"],
                    "stateName": allStations[row["stationCode"]]["stateName"],
                    "arrivalTime": row["arrivalTime"],
                    "departureTime": row["departureTime"],
                    "haltDuration": row["haltDuration"],
                    "distanceTravelled": row["distanceTravelled"],
                    "haltNumber": row["haltNumber"]
                }

                if trainNumber in stage:
                    stage[trainNumber]["route"].append(newRow)
                else:
                    stage[trainNumber] = {"route": [newRow]}

            for key in stage.keys():
                data[key] = allTrains[key]
                data[key]["trainRoute"] = stage[key]["route"]
                data[key]["stopCount"] = len(stage[key]["route"])
                data[key]["travelDistance"] = stage[key]["route"][-1]["distanceTravelled"]
                data[key] = json.dumps(data[key])
                
            hashValue = "trains"


    return [hashValue, data]

def lambda_handler(event, context):

    r = helper.cacheConnection()
    file = helper.eventFileDownloader(trigger=True, triggerEvent=event)
    helper.writeLog("info", "Data Load File:", file)
    helper.writeLog("info", "Reading source file")

    if file == "swagger.json":
        with open("/tmp/" + file, "r") as swaggerFile:
            swagger = json.loads(swaggerFile.read())
        helper.writeLog("info","Swagger specification:", swagger)
        redisHash = "swagger"
        redisBody = {
            "specification": json.dumps(swagger)
        }

    elif file in ("station.csv", "train.csv", "route.csv"):
        redisHash, redisBody = jsonGenerate(file, r)
        
    else:
        helper.writeLog("error", "Incorrect filename provided:", file)
        raise Exception()
    
    helper.cacheTransaction(
        redisClient=r,
        hashKey=redisHash,
        hashMap=redisBody
    )
    
    return "Cache Load Completed!"
