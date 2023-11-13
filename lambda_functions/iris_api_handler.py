from lib import helper
import json
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

classMapping = {
            "1A": "First Class AC",
            "2A": "Two Tier AC",
            "3A": "Three Tier AC",
            "SL": "Sleeper Class",
            "GEN": "General",
            "PWD": "Physically Challenged",
            "3E": "Three Tier AC (Economy)",
            "GRD": "General Luggage",
            "PC": "Pantry Car",
            "2S": "Second Sitting",
            "CC": "Chair Car AC",
            "EC": "Executive Chair Car",
            "EV": "Vistadome AC",
            "EA": "Anubhuti",
            "FC": "First Class Non AC"
        }

### Generate response body
def responseBody(records=[], swagger=False, incorrectParam=False, incorrectParamType="", incorrectParamValue=[]):

    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token"
    }

    if swagger:
        code = 200
        resultBody = records[0]

    elif incorrectParam:
        code = 400
        if incorrectParamType == "path":
            resultBody = {
                "message": f"Incorrect value for path parameters: {incorrectParamValue}"
            }
        elif incorrectParamType == "query":
            resultBody = {
                "message": f"Missing required request parameters: {incorrectParamValue}"
            }
        elif incorrectParamType == "station":
            resultBody = {
                "message": f"Source and Destination cannot be the same: {incorrectParamValue}"
            }

    else:
        count = len(records)
        if count == 0:
            code = 404
            message = "not found"
        else:
            code = 200
            message = "success"

        resultBody = {
                        "responseMetadata": {
                            "message": message,
                            "result": count
                        },
                        "data": records
                    }

    return {
                "statusCode": code,
                "headers": headers,
                "body":json.dumps(resultBody)
            }

def fetchSwagger():

    r = helper.cacheConnection()
    swaggerBody = helper.cacheTransaction(
        redisClient=r,
        hashKey="swagger",
        action="fetch",
        recordKey="specification"
    )

    if swaggerBody:
        return [swaggerBody]
    
    bucket = os.getenv("swagger_bucket")
    objectKey = "iris-service-api/swagger/swagger.json"
    file = helper.eventFileDownloader(
        bucket=bucket,
        key=objectKey
    )
    with open("/tmp/" + file, "r") as swaggerFile:
        swagger = json.loads(swaggerFile.read())

    helper.cacheTransaction(
        redisClient=r,
        hashKey="swagger",
        hashMap={
            "specification": json.dumps(swagger)
        }
    )

    return [swagger]

def fetchOverview():

    query = """
            select "station", count(*) from ir_train_station_trst
            union
            select "train", count(*) from ir_train_information_trin
            union
            select trst_state_name, count(trst_station_code) from ir_train_station_trst
            group by trst_state_name
            """

    try:
        dbConnector = helper.dbConnection()
        rows = helper.dbQuery(dbConnector, query)
        isError = False
    except Exception as e:
        helper.writeLog("error", "Database Transaction Failed:", str(e))
        isError = True
    finally:
        helper.dbConnection(action="close", connector=dbConnector)
    
    if isError:
        raise Exception(e)
    
    stationCount = rows[0][1]
    trainCount = rows[1][1]

    state = []
    for row in rows[2:]:
        state.append(
            {
                "name": row[0],
                "count": row[1]
            }
        )
    
    returnDict = {
        "trains": {
            "count": trainCount
        },
        "stations": {
            "count": stationCount,
            "states": state
        }
    }

    return [returnDict]

def fetchStations(code=[], all=False):

    r = helper.cacheConnection()
    result = helper.cacheTransaction(
        redisClient=r,
        hashKey="stations",
        action="fetch",
        recordKey=code,
        every=all
    )

    if result:
        if not all:
            body = [json.loads(row) for row in result]
        else:
            body = []
        
            for key in result.keys():
                result[key] = json.loads(result[key])
                body.append(
                    {
                        "stationCode": result[key]["stationCode"],
                        "stationName": result[key]["stationName"]
                    }
                )
        
        return body

    if not all:
        connect = helper.dbConnection()
        query = '''
                select * from ir_train_station_trst
                where trst_station_code = %s
                '''
        result = helper.dbQuery(connect, query, code)
        helper.dbConnection(action="close", connector=connect)

        if not result:
            return []

        # Convert -1 to empty string
        body = []
        for row in result:
            row = list(row)
            while True:
                if "-1" in row:
                    row[row.index("-1")] = ""
                else:
                    break
                
            body.append(
                {
                    "stationCode": row[0],
                    "stationName": row[1],
                    "stateName": row[2],
                    "railwaysZoneShort": row[3],
                    "railwaysZoneFull": row[4]
                }
            )
        
    else:
        connect = helper.dbConnection()
        query = '''
                select trst_station_code, trst_station_name from ir_train_station_trst
                '''
        result = helper.dbQuery(connect, query)
        helper.dbConnection(action="close", connector=connect)
        body = []
        
        for row in result:
            body.append(
                    {
                        "stationCode": row[0],
                        "stationName": row[1]
                    }
                )

    return body

def fetchTrains(number="", all=False):
    
    if not all:

        r = helper.cacheConnection()
        result = helper.cacheTransaction(
            redisClient=r,
            hashKey="trains",
            action="fetch",
            recordKey=number,
            every=all
        )
        if result:
        
            result.pop("trainRoute")
            if result["travelDistance"] == "":
                result["travelDistance"] = -1
            else:
                result["travelDistance"] = int(result["travelDistance"])
            if result["stopCount"] == "":
                result["stopCount"] = -1
            else:
                result["stopCount"] = int(result["stopCount"])
            if result["averageSpeed"] == "":
                result["averageSpeed"] = -1
            else:
                result["averageSpeed"] = int(result["averageSpeed"])
            if result["coachClass"] == "":
                result["coachClass"] = []
            else:
                result["coachClass"] = result["coachClass"].split(", ")
                classResponse = [
                    {
                        "classCode": i,
                        "className": classMapping[i] 
                    } for i in result["coachClass"]
                ]
                result["coachClass"] = classResponse
            if result["serviceDays"] == "":
                result["serviceDays"] = []
            else:
                if "and" in result["serviceDays"]:
                    result["serviceDays"] = result["serviceDays"].replace(" and", ",")
                    result["serviceDays"] = result["serviceDays"].split(", ")
                elif "," in result["serviceDays"]:
                    result["serviceDays"] = result["serviceDays"].split(", ")
                else:
                    result["serviceDays"] = [result["serviceDays"]]
            
            return [result]

        connect = helper.dbConnection()
        query = '''
                select
	                t.trin_train_number,
	                t.trin_train_name,
	                t.trin_source_station,
	                ss.trst_station_name,
	                t.trin_destination_station,
	                sd.trst_station_name,
	                t.trin_train_type,
	                t.trin_service_days,
	                t.trin_train_coach_class,
	                t.trin_travel_duration,
	                t.trin_travel_distance,
	                t.trin_number_of_stops,
	                t.trin_average_speed
                from ir_train_information_trin t
                left join ir_train_station_trst ss
                on t.trin_source_station = ss.trst_station_code
                left join ir_train_station_trst sd
                on t.trin_destination_station = sd.trst_station_code
                where t.trin_train_number = %s
                '''
        result = helper.dbQuery(connect, query, [number])
        if not result:
            body = []
        else:
            result = list(result[0])
            while True:
                if "-1" in result:
                    result[result.index("-1")] = ""
                else:
                    break
            if result[10] == -1:
                query = '''
                        select trro_distance_travelled from ir_train_route_trro r
                        inner join ir_train_information_trin t
                        on t.trin_train_number = r.trro_train_number
                        where t.trin_train_number = %s and trro_departure_time = "DESTINATION"
                        '''
                distance = helper.dbQuery(connect, query, [number])
                if distance:
                    result[10] = distance[0][0]
            if result[11] == -1:
                query = '''
                        select count(*) from ir_train_route_trro r
                        inner join ir_train_information_trin t
                        on t.trin_train_number = r.trro_train_number
                        where t.trin_train_number = %s
                        '''
                stops = helper.dbQuery(connect, query, [number])
                if stops:
                    result[11] = stops[0][0]

            if result[8] == "":
                classResponse = []
            else:
                result[8] = result[8].split(", ")
                classResponse = [
                    {
                        "classCode": i,
                        "className": classMapping[i] 
                    } for i in result[8]
                ]

            if result[7] == "":
                result[7] = []
            else:
                if "and" in result[7]:
                    result[7] = result[7].replace(" and", ",").split(", ")

                elif "," in result[7]:
                    result[7] = result[7].split(", ")

                else:
                    result[7] = [result[7]]
            
            body = [{
                "trainNumber": result[0],
                "trainName": result[1],
                "sourceStationCode": result[2],
                "sourceStationName": result[3],
                "destinationStationCode": result[4],
                "destinationStationName": result[5],
                "trainType": result[6],
                "serviceDays": result[7],
                "coachClass": classResponse,
                "travelDuration": result[9],
                "travelDistance": result[10],
                "stopCount": result[11],
                "averageSpeed": result[12]
            }]
        helper.dbConnection(action="close", connector=connect)
        helper.cacheTransaction(
            redisClient=r,
            hashKey="trains",
            hashMap={
                number: json.dumps(body[0])
            }
        )
        
    else:
        connect = helper.dbConnection()
        query = '''
                select trin_train_number, trin_train_name from ir_train_information_trin
                '''
        result = helper.dbQuery(connect, query)
        helper.dbConnection(action="close", connector=connect)
        body = []
        
        for row in result:
            body.append(
                    {
                        "trainNumber": row[0],
                        "trainName": row[1]
                    }
                )

    return body

def fetchTrainRoute(number, code=""):

    r = helper.cacheConnection()
    result = helper.cacheTransaction(
        redisClient=r,
        hashKey="trains",
        action="fetch",
        recordKey=number
    )

    if result:
        if code:
            routeDetail = list(filter(lambda route: route["stationCode"] == code, result["trainRoute"]))[0]
            if routeDetail["arrivalTime"] != "SOURCE":
                routeDetail["arrivalTime"] = routeDetail["arrivalTime"].zfill(8)
            if routeDetail["departureTime"] != "DESTINATION":
                routeDetail["departureTime"] = routeDetail["departureTime"].zfill(8)

            routeDetail["haltDuration"] = int(routeDetail["haltDuration"])
            routeDetail["distanceTravelled"] = int(routeDetail["distanceTravelled"])
            routeDetail["haltNumber"] = int(routeDetail["haltNumber"])

            body = [
                {
                    "trainNumber": number,
                    "trainName": result["trainName"],
                    "trainRoute": [routeDetail]
                }
            ]
            
        else:
            for route in result["trainRoute"]:
                if route["arrivalTime"] != "SOURCE":
                    route["arrivalTime"] = route["arrivalTime"].zfill(8)
                if route["departureTime"] != "DESTINATION":
                    route["departureTime"] = route["departureTime"].zfill(8)
                route["haltDuration"] = int(route["haltDuration"])
                route["distanceTravelled"] = int(route["distanceTravelled"])
                route["haltNumber"] = int(route["haltNumber"])
            
            body = [
                {
                    "trainNumber": number,
                    "trainName": result["trainName"],
                    "trainRoute": result["trainRoute"]
                }
            ]

        return body

    if code:
        extraQuery = "and r.trro_route_station = %s"
        params = [number, code]
    else:
        extraQuery = ""
        params = [number]
    
    connect = helper.dbConnection()
    query = f'''
            select
            	r.trro_train_number,
            	t.trin_train_name,
            	r.trro_route_station,
            	s.trst_station_name,
            	s.trst_state_name,
            	r.trro_arrival_time,
            	r.trro_departure_time,
            	r.trro_halt_duration,
            	r.trro_distance_travelled,
            	r.trro_halt_number
            from ir_train_route_trro r
            inner join ir_train_information_trin t
            on t.trin_train_number = r.trro_train_number
            inner join ir_train_station_trst s
            on s.trst_station_code = r.trro_route_station
            where r.trro_train_number = %s {extraQuery}
            '''
    results = helper.dbQuery(connect, query, params)
    body = {}
    if results:
        route = []
        for result in results:
            result = list(result)
            if result[5] != "SOURCE":
                result[5] = result[5].zfill(8)
            if result[6] != "DESTINATION":
                result[6] = result[6].zfill(8)

            route.append(
                {
                    "stationCode": result[2],
                    "stationName": result[3],
                    "stateName": result[4],
                    "arrivalTime": result[5],
                    "departureTime": result[6],
                    "haltDuration": result[7],
                    "distanceTravelled": result[8],
                    "haltNumber": result[9]
                }
            )
        body = {
            "trainNumber": number,
            "trainName": results[0][1],
            "trainRoute": route
        }

    return [body]

def fetchTrainAvailabilty(source, destination, dateString):
    
    url = "https://railways.easemytrip.com/TrainListInfo/({})-to-({})/2/{}".format(source, destination, dateString)
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    # Get list of available train numbers
    numberData = soup.find_all("div", {"class":"tr-no"})
    numberList = [i.get_text().strip() for i in numberData]
    if not numberList:
        return []
    parentAvailability = []

    r = helper.cacheConnection()
    trainList = helper.cacheTransaction(
            redisClient=r,
            hashKey="trains",
            action="fetch",
            recordKey=numberList
        )

    for i in range(len(numberList)):
        # Get train name from train number
        availability = {}
        trainName = json.loads(trainList[i])["trainName"]
        
        # Get source and destination station codes
        data = soup.find_all("div", {"class": "topdiv"})[i]
        stations = data.find_all("span", {"class": "routx"})
        
        # Get station name from station code
        sourceCode = stations[0].get_text().strip()
        destinationCode = stations[1].get_text().strip()
        stationList = helper.cacheTransaction(
            redisClient=r,
            hashKey="stations",
            action="fetch",
            recordKey=[sourceCode, destinationCode]
        )
        sourceStation = json.loads(stationList[0])["stationName"]
        destinationStation = json.loads(stationList[1])["stationName"]

        # Get distance travelled between source and destination
        stations = list(filter(lambda route: route["stationCode"] in [sourceCode, destinationCode], json.loads(trainList[i])["trainRoute"]))
        sourceDistance = int(stations[0]["distanceTravelled"])
        destinationDistance = int(stations[1]["distanceTravelled"])
        distance = destinationDistance - sourceDistance

        data = soup.find_all("div", {"class": "bodydiv"})[i]
        times = data.find_all("div", {"class": "tr-col-2"})
        dates = []
        # Get arrival and departure time
        for t in times:

            datePart = t.find_all("div", {"class": "tr-statn"})[1].get_text().split(", ")[1]
            timePart = t.find("div", {"class": "tr-tme"}).get_text()
            concatTime = datetime.strptime(datePart + " " + timePart, "%d %B %Y %H:%M")
            concatTimeString = concatTime.strftime("%d %B %Y %I:%M %p")
            dates.append(concatTimeString)
    
        duration = data.find("div", {"class": "label tl ng-binding"}).get_text().strip()

        availability["trainNumber"] = numberList[i]
        availability["trainName"] = trainName
        availability["sourceStationCode"] = sourceCode
        availability["sourceStationName"] = sourceStation
        availability["departureTime"] = dates[0]
        availability["destinationStationCode"] = destinationCode
        availability["destinationStationName"] = destinationStation
        availability["arrivalTime"] = dates[1]
        availability["duration"] = duration
        availability["distanceTravelled"] = distance
        helper.writeLog("success", "Train information fetched")

        idTag = "divTran_price{{'%s'}}" % str(numberList[i])
        # Get class data
        classes = soup.find("div", {"id": idTag}).find("div", {"class": "seatavl"}).find_all("div", {"class": "train-fare-item-row"})
        availabilityList = []
        
        for i in range(0, len(classes), 2):
            classCode = classes[i].find("span", {"class": "train-class"}).find_all("span")[1].get_text()
            # If classCode is not present, then its junk
            if not classCode:
                break

            className = classMapping[classCode]

            classFare = classes[i].find("span", {"class": "train-fare"}).get_text().strip()
            # classFare contains the rupee symbol
            if not classFare:
                try:
                    classFare = classes[i+1].find("span").find_all("span")[1].get_text().strip()
                    helper.writeLog("info", "Class fare fetched")
                except IndexError:
                    classFare = 0
                    helper.writeLog("warning", "Class fare is not available")
            else:
                classFare = classFare[1:]

            avail = classes[i+1].find("div").get_text()
            if avail == "Click To Refresh":
                avail = "DATA NOT AVAILABLE"
                helper.writeLog("warning", "Availability data is not available")
            
            availabilityList.append(
                {
                    "classCode": classCode,
                    "className": className,
                    "classFare": int(classFare),
                    "classAvailability": avail
                }
            )
            helper.writeLog("success", "Class information fetched")
        availability["class"] = availabilityList
        parentAvailability.append(availability)

    return parentAvailability  

def fetchTrainStatus(number):

    train = fetchTrainRoute(number)
    routeList = train[0]["trainRoute"]

    for route in routeList:
        del route["haltDuration"]
        del route["distanceTravelled"]
        del route["haltNumber"]

    url = f"https://www.trainman.in/running-status/{number}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    # Journey start date of the train
    startDateString = soup.find("div", {"class": "nav-link p-1 active"}).get_text().strip() + " 2023"
    startDate = datetime.strptime(startDateString, "%d %b %Y")

    trainStatus = {
        "trainNumber": number,
        "trainName": train[0]["trainName"],
        "journeyStartDate": startDate.strftime("%d %B %Y")
    }

    currentDate = datetime.now()
    daysBetween = (currentDate - startDate).days
    if daysBetween > 1:
        jouneyMessage = "Cannot show past journey prior to yesterday"
        statusList = []
    else:
        if daysBetween == 0:
            jouneyMessage = "Journey started today"
        else:
            jouneyMessage = "Journey started yesterday"
    
        data = soup.find("tbody", {"_ngcontent-sc192": ""}).find_all("tr")
        statusList = []
        intermediate = 0
        for i in range(len(routeList)):
            stationData = data[i].find_all("td")

            # Current train station
            current = stationData[4].find("div", {"class": "text-muted ng-star-inserted"})
            if current:
                if i == 0:
                    jouneyMessage = "Journey has not started"
                    statusList.append(routeList[0])
                break

            # Day count of journey
            day = int(stationData[1].find("div", {"style": "font-size: 11px; color: gray;"}).get_text().split(" ")[4][0])

            # Fetch delay
            delayData = stationData[4].find("div", {"class": "text-success ng-star-inserted"})
            if not delayData:
                delayData = stationData[4].find("div", {"class": "text-danger ng-star-inserted"})

            delay = delayData.get_text().strip().replace("hr", "h").replace("min", "m")


            # Fetch actual arrival and departure dates
            times = stationData[3].find_all("time")
            timeList = []
            for t in range(2):
                actualTime = times[t].get_text()
                timeType = ["arrivalTime", "departureTime"]

                if actualTime in ("Source", "Destination"):
                    actualTime = actualTime.upper()
                elif actualTime == "UA" and delay == "No Delay":
                    actualTime = routeList[i][timeType[t]]
                elif actualTime == "UA" and delay != "No Delay":
                    expected = routeList[i][timeType[t]]
                    if "h" in delay:
                        delayHr = delay.split(" ")[0]
                        delayMin = delay.split(" ")[2]
                    else:
                        delayHr = 0
                        delayMin = delay.split(" ")[0]
                    expectedTime = datetime.strptime(expected, "%I:%M %p") + timedelta(hours=int(delayHr), minutes=int(delayMin))
                    actualTime = expectedTime.strftime("%I:%M %p")
                else:
                    actualTime = datetime.strptime(actualTime, "%H:%M").strftime("%I:%M %p")
                timeList.append(actualTime)

            statusList.append(
                {
                    "stationCode": routeList[i]["stationCode"],
                    "stationName": routeList[i]["stationName"],
                    "stateName": routeList[i]["stateName"],
                    "expectedArrivalTime": routeList[i]["arrivalTime"],
                    "actualArrivalTime": timeList[0],
                    "expectedDepartureTime": routeList[i]["departureTime"],
                    "actualDepartureTime": timeList[1],
                    "delay": delay,
                    "day": day,
                    "intermediateStation": intermediate
                }
            )
            # Intermediate stations in-between
            if i != len(routeList) - 1:
                intermediate = int(stationData[1].find("div", {"class": "intermediateStation"}).get_text().split(" ")[1])
        
    trainStatus["journeyMessage"] = jouneyMessage
    trainStatus["status"] = statusList
    return [trainStatus]


def lambda_handler(event, context):

    helper.writeLog("info", "API Resource:", event["resource"])
    helper.writeLog("info", "HTTP Method:", event["httpMethod"])

    if event["resource"] == "/v2/railways/swagger":
        swaggerList = fetchSwagger()
        return responseBody(swaggerList, swagger=True)

    if event["resource"] == "/v2/railways/overview":
        dataList = fetchOverview()

    elif event["resource"] == "/v2/railways/stations":
        station = event["queryStringParameters"]["stationCode"]
        if "," in station:
            codeList = [code.upper().strip() for code in station.split(",")]
        else:
            codeList = [station.upper()]
        dataList = fetchStations(codeList)

    elif event["resource"] == "/v2/railways/stations/codes":
        dataList = fetchStations(all=True)

    elif event["resource"] == "/v2/railways/trains":
        train = event["queryStringParameters"]["trainNumber"]
        if train:
            dataList = fetchTrains(train)
        else:
            dataList = []

    elif event["resource"] == "/v2/railways/trains/numbers":
        dataList = fetchTrains(all=True)

    elif event["resource"] == "/v2/railways/route/{type}":

        request = event["pathParameters"]["type"]
        
        if request == "station":
            if "stationCode" in event["queryStringParameters"]:
                train = event["queryStringParameters"]["trainNumber"]
                station = event["queryStringParameters"]["stationCode"]
                if train and station:
                    dataList = fetchTrainRoute(train, station.upper())
                else:
                    dataList = []
            else:
                return responseBody(incorrectParam=True, incorrectParamType="query", incorrectParamValue=["stationCode"])
        
        elif request == "all":
            train = event["queryStringParameters"]["trainNumber"]
            if train:
                dataList = fetchTrainRoute(train)
            else:
                dataList = []

        else:
            return responseBody(incorrectParam=True, incorrectParamType="path", incorrectParamValue=["type"])
        
    elif event["resource"] == "/v2/railways/route/availability":
        source = event["queryStringParameters"]["sourceStation"]
        destination = event["queryStringParameters"]["destinationStation"]
        if source.upper() == destination.upper():
            return responseBody(incorrectParam=True, incorrectParamType="station", incorrectParamValue=[source, destination])
        
        journeyDate = event["queryStringParameters"]["journeyDate"]
        dataList = fetchTrainAvailabilty(source.upper(), destination.upper(), journeyDate)

    elif event["resource"] == "/v2/railways/trains/status":
        train = event["queryStringParameters"]["trainNumber"]
        dataList = fetchTrainStatus(train)

    return responseBody(dataList)

