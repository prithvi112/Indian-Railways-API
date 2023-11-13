from lib import helper
import pandas as pd
import os

def dataProcessor(csvPath, entity):

    helper.writeLog("warning", "Processing Source File:", csvPath)

    df = pd.read_csv(csvPath)
    df = df.where(pd.notnull(df), "-1")
    df = df.astype(str)

    if entity == "Train":
        numColumns = ["trin_travel_distance", "trin_number_of_stops", "trin_average_speed"]
        df[numColumns] = df[numColumns].apply(pd.to_numeric)
        df["trin_train_number"] = df["trin_train_number"].str.zfill(5)

    elif entity == "Route":
        numColumns = ["trro_halt_duration", "trro_distance_travelled", "trro_halt_number"]
        df[numColumns] = df[numColumns].apply(pd.to_numeric)
        df["trro_train_number"] = df["trro_train_number"].str.zfill(5)

    helper.writeLog("success", "Source File Processed")
    
    dataList = df.values.tolist()
    helper.writeLog("info", "Processor Output:", dataList)
    return dataList


fileTableMapping = {
    "station.csv": ["Station", "ir_train_station_trst"],
    "train.csv": ["Train", "ir_train_information_trin"],
    "route.csv": ["Route", "ir_train_route_trro"]
}

def lambda_handler(event, context):

    ### Download file from S3
    file = helper.eventFileDownloader(event)

    if file not in ("station.csv", "train.csv", "route.csv"):
        helper.writeLog("error", "Incorrect filename provided:", file)

    else:
        helper.writeLog("info", "Data Load Entity:", fileTableMapping[file][0])
        helper.writeLog("info", "Data Load Table:", fileTableMapping[file][1])

        ### Convert CSV file to nested list
        data = dataProcessor("/tmp/" + file, fileTableMapping[file][0])
        helper.writeLog("info", "Number of Rows:", len(data))
        
        ### Perform database load operation
        if file == "station.csv":
            query = f"""
                    INSERT INTO {fileTableMapping[file][1]}
                    VALUES (%s, %s, %s, %s, %s)
                    """
            
        elif file == "train.csv":
            query = f"""
                    INSERT INTO {fileTableMapping[file][1]}
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
            
        elif file == "route.csv":
            query = f"""
                    INSERT INTO {fileTableMapping[file][1]} (trro_train_number, trro_route_station, trro_arrival_time, trro_departure_time, trro_halt_duration, trro_distance_travelled, trro_halt_number)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """
        try:
            dbConnector = helper.dbConnection()
            helper.dbQuery(dbConnector, query, data, True, True)
            isError = False
        except Exception as e:
            helper.writeLog("error", "Database Transaction Failed:", str(e))
            isError = True
        finally:
            helper.dbConnection(action="close", connector=dbConnector)

        if isError:
            raise Exception(e)
        
    return "Data Load Completed!"
