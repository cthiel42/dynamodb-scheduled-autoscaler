import json
import boto3
import datetime
import os

def lambda_handler(event, context):
    client = boto3.client('application-autoscaling',region_name=os.environ['AWS_REGION'])
    file = open('config.json','r')
    config = file.read()
    file.close()
    config = json.loads(config)
    
    for operation in config:
        print(operation.get("resource"))
        # determine what scaling settings should be at default
        readMin = operation.get("defaultReadMin")
        readMax = operation.get("defaultReadMax")
        writeMin = operation.get("defaultWriteMin")
        writeMax = operation.get("defaultWriteMax")
        currentTime = datetime.datetime.utcnow()
        for interval in operation.get("intervals"):
            # Check whether we're in any intervals that will overwrite the existing capacity
            intervalStart = datetime.datetime.strptime(interval.get("timeStart"),"%H:%M:%S")
            intervalEnd = datetime.datetime.strptime(interval.get("timeEnd"),"%H:%M:%S")
            intervalStart = intervalStart.replace(year=currentTime.year,month=currentTime.month,day=currentTime.day)
            intervalEnd = intervalEnd.replace(year=currentTime.year,month=currentTime.month,day=currentTime.day)
            
            # Currently won't handle overlapping intervals. Could write it in the future to take the greatest min/max values it sees
            if intervalStart <= currentTime and currentTime < intervalEnd:
                readMin = interval.get("readMin",readMin)
                readMax = interval.get("readMax",readMax)
                writeMin = interval.get("writeMin",writeMin)
                writeMax = interval.get("writeMax",writeMax)
            
        print("Determined the following values should be set: ")
        print("readMin: "+str(readMin))
        print("readMax: "+str(readMax))
        print("writeMin: "+ str(writeMin))
        print("writeMax: "+str(writeMax))

        dimension = 'dynamodb:' + operation.get("type") + ':ReadCapacityUnits'
        response = client.describe_scalable_targets(
            ServiceNamespace='dynamodb',
            ScalableDimension=dimension,
            ResourceIds=[
                operation.get("resource")
            ],
            MaxResults=10,
        )

        if len(response.get("ScalableTargets",[])) == 1 and readMin != response.get("ScalableTargets")[0].get("MinCapacity") or readMax != response.get("ScalableTargets")[0].get("MaxCapacity"):
            print("Updating Read Capacity Units:")
            print("ReadMin: "+str(response.get("ScalableTargets")[0].get("MinCapacity")) + " -> " + str(readMin))
            print("ReadMax: "+str(response.get("ScalableTargets")[0].get("MaxCapacity")) + " -> " + str(readMax))
            response = client.register_scalable_target(
                ServiceNamespace='dynamodb',
                ResourceId=operation.get("resource"),
                ScalableDimension=dimension,
                MinCapacity=readMin,
                MaxCapacity=readMax
            )

        dimension = 'dynamodb:' + operation.get("type") + ':WriteCapacityUnits'
        response = client.describe_scalable_targets(
            ServiceNamespace='dynamodb',
            ScalableDimension=dimension,
            ResourceIds=[
                operation.get("resource")
            ],
            MaxResults=10,
        )

        if len(response.get("ScalableTargets",[])) == 1 and writeMin != response.get("ScalableTargets")[0].get("MinCapacity") or writeMax != response.get("ScalableTargets")[0].get("MaxCapacity"):
            print("Updating Write Capacity Units:")
            print("WriteMin: "+str(response.get("ScalableTargets")[0].get("MinCapacity")) + " -> " + str(writeMin))
            print("WriteMax: "+str(response.get("ScalableTargets")[0].get("MaxCapacity")) + " -> " + str(writeMax))
            response = client.register_scalable_target(
                ServiceNamespace='dynamodb',
                ResourceId=operation.get("resource"),
                ScalableDimension=dimension,
                MinCapacity=writeMin,
                MaxCapacity=writeMax
            )
    
    return {
        'statusCode': 200,
        'body': json.dumps('Lambda exited successfully')
    }
