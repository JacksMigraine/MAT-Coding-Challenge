import paho.mqtt.client as mqtt
from math import sin, cos, sqrt, atan2, radians
import json
from typing import NamedTuple
from collections import defaultdict
from datetime import datetime
import random


class Location(NamedTuple):
    lat: float
    lon: float


class CarData(NamedTuple):
    index: int
    location: Location
    time: datetime


broker = "localhost"
# port
port = 1883
# time to live
timelive = 60
num_cars = 6
current_loc = {}
last_timestamp = {}
total_distance = dict((i, 0.0) for i in range(num_cars))
current_positions = [i for i in range(num_cars)]
num_updates = 0


def get_delta_distance(index, location):
    to_return = 0.0
    if index in current_loc.keys():
        to_return = calc_distance(current_loc[index], location)

    current_loc[index] = location
    return to_return


def get_velocity(index, distance, time):
    to_return = 0.0
    if index in last_timestamp.keys():
        to_return = calc_velocity(distance, last_timestamp[index], time)

    last_timestamp[index] = time
    return to_return


def calc_distance(loc1, loc2):
    R = 3958.8  # Radius of the earth in miles
    dLat = radians(loc2.lat - loc1.lat)
    dLon = radians(loc2.lon - loc1.lon)
    rLat1 = radians(loc1.lat)
    rLat2 = radians(loc2.lat)
    a = sin(dLat / 2) * sin(dLat / 2) + cos(rLat1) * cos(rLat2) * sin(dLon / 2) * sin(dLon / 2)
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    d = R * c  # Distance in miles
    return d


def calc_velocity(dist, time_start, time_end):
    return (dist / (time_end - time_start).microseconds) * 3600000000 if time_end > time_start else 0


def calc_position(index, distance, timestamp, velocity):
    global current_positions, num_updates
    total_distance[index] += distance
    num_updates += 1
    new_positions = [key for (key, value) in sorted(total_distance.items(), reverse=True, key=lambda x: x[1])]
    publish_status_position(index, new_positions.index(index), timestamp)
    if num_updates % num_cars == 0 and not new_positions == current_positions:
        for i in range(num_cars):
            if not new_positions[i] == current_positions[i]:
                old_position = current_positions.index(new_positions[i])
                if i < old_position:
                    publish_event_overtake(new_positions[i], new_positions[i + 1:old_position + 1], timestamp, i,
                                           velocity)

        current_positions = new_positions


def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe("carCoordinates")


def publish_event_overtake(car, overtook, time, position, velocity):
    races = ["races", "zooms", "speeds"]
    ahead = ["ahead", "past", "beyond", "clear", "free"]
    overtake = "Car {}".format(overtook[0])
    for i in range(1, len(overtook) - 1):
        overtake += ", Car {}".format(overtook[i])
    if len(overtook) > 1:
        overtake += " and Car {}".format(overtook[-1])
    verb = random.choice(["dramatic", "breathtaking", "climatic", "thrilling", "tense"])
    if velocity > 100:
        verb = random.choice(["high-speed", "rapid", "flat-out", "speedy", "reckless", "dangerous"])
    if velocity < 40:
        verb = random.choice(["skillfull", "technical", "sublime", "expert", "impressive"])
    bypass = ["overtake", "bypass", "maneuver"]
    fluff = "."
    if position == 0:
        fluff = random.choice([" to take the lead!", " claiming first place!", " coming in first."])
    text = "Car {} {} {} of {} in a {} {}{}".format(car, random.choice(races), random.choice(ahead), overtake, verb,
                                                     random.choice(bypass), fluff)
    message = {"timestamp": time, "text": text}
    client.publish("events", json.dumps(message))


def publish_status_speed(index, speed, time):
    message = {"timestamp": time, "carIndex": index, "type": "SPEED", "value": speed}
    client.publish("carStatus", json.dumps(message))


def publish_status_position(index, position, time):
    message = {"timestamp": time, "carIndex": index, "type": "POSITION", "value": position}
    client.publish("carStatus", json.dumps(message))


def on_message(client, userdata, msg):
    message = json.loads(msg.payload.decode())
    car_update = CarData(message['carIndex'], Location(message['location']['lat'], message['location']['long']),
                         datetime.utcfromtimestamp(message['timestamp'] / 1000))
    distance = get_delta_distance(car_update.index, car_update.location)
    velocity = get_velocity(car_update.index, distance, car_update.time)
    publish_status_speed(car_update.index, velocity, message['timestamp'])
    calc_position(car_update.index, distance, message['timestamp'], velocity)


client = mqtt.Client()
client.connect(broker, port, timelive)
client.on_connect = on_connect
client.on_message = on_message
client.loop_forever()
