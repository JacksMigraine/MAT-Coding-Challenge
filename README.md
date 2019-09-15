# MAT-Coding-Challenge
My implementation of the MAT challenge. I decided to use Python becuse there is extensive documentaion for creating a MQTT client and it was quick to setup and easy to get running.

## Dependencies:
* python3.6
* paho.mqtt (pip install paho-mqtt)

## To Run:
Once the MQTT broker is up run:
```console
python3.6 CarTracker.py
```

## How it works
An MQTT client is created and listens to the CarCoordinates topic. Evey time a mesage is received on this topic the following steps are done:
1. Caulculate distance travelled - this is done by comparing each cars coordinate with its previous coordinate and some maths.
2. Calculate velocity - this is done using the distance traveled and the time taken between this and the previous update for each car.
3. Publish speed - the velocity calculated above is published to carStatus.
4. Calculate position - the position of each car is determined by the total distance each car has travelled. The car that has travelled the most distance is assumed to be the one coming first etc. This is just an approximation and requires the app to run from the start of the race to be accurate.
5. Publish position - the calculated above is pushed to carStatus.
6. Determine if events occur. Events are exclusively overtakes. Overtakes are determined by comparing the positions now to the positions historically. If this does occur a summary is published on the "events" topic. Factors such as speed and position have an effect on the event message.


