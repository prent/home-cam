import boto3
import datetime
from botocore.client import Config
from requests import Request, Session
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import time
import json
from picamera import PiCamera
from time import sleep
import os

topicName = "YOUR-TOPIC-NAME"
iotEndpoint = "YOUR-ENDPOINT"
deviceName = "DEVICE-NAME/ID"

camera = PiCamera()

#------------ START S3 -------------
# Create S3 client object
s3 = boto3.client('s3', config=Config(signature_version='s3v4', region_name='eu-west-1'))
s3Client = boto3.client('s3')

# Define bucket and key name
YOUR_BUCKET = 'S3-BUCKET-NAME'
KEY_NAME = 'KEY-NAME'
YOUR_KMS_KEY_ID = 'KMS-KEY'

fileName = '/home/pi/Desktop/tempfile.jpg'


def removePhoto():
    print("Removing Photo locally")
    os.remove(fileName)
    print("Done")

def uploadPhotoToS3():
    print("\n\nUploading photo to S3...")
    PATH_TO_LOCAL_FILE = fileName

    with open(PATH_TO_LOCAL_FILE, 'rb') as readFile:
       file = readFile.read()
    response = s3Client.put_object(
    ACL='public-read',
    Body=file,
    Bucket=YOUR_BUCKET,
    ContentType='image/jpg',
    GrantWriteACP='string',
    Key=KEY_NAME+ str(datetime.datetime.now()) + ".jpg",
    Metadata={
        'Content-Type': 'image/jpg'
    }
)

    print("Response: " + json.dumps(response.text))
    print("Upload done")
    #Remove photo from local storage.
    removePhoto()



def takePhoto():
    print("Taking photo")
    camera.start_preview()
    sleep(1)
    camera.capture(fileName)
    camera.stop_preview()
    uploadPhotoToS3()

# ------------------------------ Start IOT stuff ------------------------------
def customCallback(client, userdata, message):
    print("Received a new message: ")
    print(message.payload)
    print("from topic: ")
    print(message.topic)
    print("--------------\n\n")
    #Whenever the device gets a message from AWS IoT, take a photo. 
    takePhoto()

print("-- Starting App --")
myMQTTClient = AWSIoTMQTTClient(deviceName)
myMQTTClient.configureEndpoint(iotEndpoint, 8883)
myMQTTClient.configureCredentials("root-ca.pem", "xx-private.pem.key", "xx-certificate.pem.crt")
myMQTTClient.configureAutoReconnectBackoffTime(1, 32, 20)
myMQTTClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
myMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
myMQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
myMQTTClient.configureMQTTOperationTimeout(5) # 5 sec

#Connecting to IOT 
myMQTTClient.connect()
myMQTTClient.subscribe(topicName, 1, customCallback)
time.sleep(2)
loopCount = 0
#Always Listen
while True:
    loopCount += 1    
    time.sleep(1)

