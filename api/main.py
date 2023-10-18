from flask import Flask, request
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from bson import json_util


load_dotenv()
mongo_connection = os.getenv('MONGO_CONNECTION')
client = MongoClient(mongo_connection)
class_collection = client['Events']['Classes']
participant_collection = client['Events']['Participants']
presence_collection = client['Events']['PresenceLog']
users_collection = client['Users']['Students']

app = Flask(__name__)

@app.route("/", methods=['GET'])
def home_route():
    return "Hello World"


@app.route("/getclasses", methods=['GET'])
def get_classes():
    return list(class_collection.find({},{"_id": 0}))

@app.route("/deleteclass/<class_id>", methods=['DELETE'])
def delete_class(class_id):
    result = class_collection.delete_one({"id": class_id})
    participant_collection.delete_one({"classId": class_id})
    return "Success" if result.deleted_count else "Failed"

@app.route("/includeclass", methods=['POST'])
def set_new_class():
    class_name = request.json['className']
    class_weekday = request.json['weekday']
    class_professor = request.json['professor']
    class_hour = request.json['hour']
    class_color = request.json['color']
    class_building = request.json['building']
    class_room = request.json['room']
    class_list = list(class_collection.find({}))
    highest_id = 0
    for item in class_list:
        highest_id = item['id'] if item['id'] > highest_id else highest_id
    result = class_collection.insert_one({ "id": highest_id + 1, "className": class_name, "weekday":class_weekday, "professor": class_professor,\
                                           "building": class_building, "room": class_room,"hour": class_hour, "color": class_color, "haveParticipantList": False }).inserted_id
    return f'{highest_id + 1}' if result is not None else "Failed"

@app.route("/insertparticipantlist", methods=['POST'])
def insert_participant_list():
    class_id = request.json['id']
    participant_list = request.json['participantList']
    result = participant_collection.insert_one({"classId": class_id, "participantList": participant_list }).inserted_id
    for participant in participant_list:
        users_collection.update_one({"RA": int(participant)}, {"$push": {"classesIn": class_id}})
    if result:
        class_collection.update_one({"id": int(class_id)}, { "$set": { "haveParticipantList": True}})
    return "Success" if result is not None else "Failed"

@app.route("/getparticipantlist/<class_id>", methods=['GET'])
def get_participant_list(class_id):
    return participant_collection.find_one({"classId": int(class_id)}, {"_id": 0})['participantList']


@app.route("/editparticipantlist", methods=['PUT'])
def edit_participant_list():
    class_id = request.json['id']
    participant_list = request.json['participantList']
    for participant in participant_list:
        users_collection.update_one({"RA": int(participant)}, {"$addToSet": {"classesIn": class_id}})
    result = participant_collection.update_one({"classId": class_id}, {"$set": { "participantList": participant_list}})
    return "Success" if result.modified_count is not None else "Failed"

@app.route("/openpresencelog", methods=['POST'])
def open_presence_log():
    class_id = request.json['id']
    date = request.json['date']
    participant_object = participant_collection.find_one({"classId": int(class_id)}, {"_id": 0})
    if participant_object is None: 
        return "Nenhuma lista de participantes foi encontrada"
    presence_log = { "classId": class_id, "openWindow": True, "date": int(date), "presencePercentage": 0, "numberOfTotalParticipants": len(participant_object['participantList']), "numberOfParticipants": 0 }
    for ra in participant_object['participantList']:
        presence_log[ra] = False
    result = presence_collection.insert_one(presence_log).inserted_id
    return "Success" if result is not None else 'Failed'

@app.route("/reopenpresencelog", methods=['PUT'])
def reopen_presence_log():
    class_id = request.json['id']
    date = request.json['date']
    update_log = {"$set": { "openWindow": True}}
    result = presence_collection.update_one({"classId": int(class_id), "date": int(date)}, update_log)
    return "Success" if result.modified_count is not None else 'Failed'

@app.route("/validatepresence", methods=['PUT'])
def validate_presenc():
    class_id = request.json['id']
    date = request.json['date']
    user_ra = request.json['ra']
    presence = presence_collection.find_one({"classId": int(class_id), "date": int(date)}, {"_id": 0})

    if presence['openWindow'] and user_ra in presence:
        update_presence = {"$set": {user_ra: True}}
        result = presence_collection.update_one({"classId": int(class_id), "date": int(date) }, update_presence)
        return "Success" if result.modified_count else 'Failed'
    else:
        return "Presence Validation Window is Closed"

def is_ra(ra):
    return True if ra.isnumeric() and len(ra) == 8 else False

def calculate_presence(presence, participant_obj):
    ra_number = int(presence['numberOfTotalParticipants'])
    presence_counter = 0
    for key, value in presence.items():
        if (key in participant_obj['participantList']) and is_ra(key) and value:
            presence_counter += 1
    return (presence_counter, (presence_counter / ra_number) * 100 if ra_number > 0 else 0)

@app.route("/closepresencelog", methods=['PUT'])
def close_presence_log():
    class_id = request.json['id']
    date = request.json['date']
    participant_obj = participant_collection.find_one({"classId": int(class_id)})
    presence = presence_collection.find_one({"classId": int(class_id), "date": int(date)})
    (presence_counter, calculated_presence) = calculate_presence(presence, participant_obj)
    close_presence = {"$set": {"openWindow": False, "presencePercentage": int(calculated_presence), "numberOfParticipants": int(presence_counter)}}
    result = presence_collection.update_one({"classId": int(class_id), "date": int(date)}, close_presence)
    return f'{calculated_presence}' if result.modified_count else 'Failed'

@app.route("/getpresencelog/<class_id>/<date>", methods=['GET'])
def get_presence_log(class_id, date):
    result = presence_collection.find_one({"classId": int(class_id), "date": int(date)}, {"_id": 0})
    return result if result is not None else "Not Found"
