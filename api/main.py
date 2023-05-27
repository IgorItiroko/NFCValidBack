from flask import Flask, request
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import json
from bson import json_util


load_dotenv()
mongo_connection = os.getenv('MONGO_CONNECTION')
client = MongoClient(mongo_connection)
class_collection = client['Events']['Classes']
participant_collection = client['Events']['Participants']
presence_collection = client['Events']['PresenceLog']

app = Flask(__name__)

@app.route("/", methods=['GET'])
def home_route():
    return "Hello World"


@app.route("/getclasses", methods=['GET'])
def get_classes():
    return list(class_collection.find({},{"_id": 0}))

    

@app.route("/includeclass", methods=['POST'])
def set_new_class():
    class_name = request.json['className']
    class_weekday = request.json['weekday']
    class_professor = request.json['professor']
    class_hour = request.json['hour']
    class_color = request.json['color']
    class_list = list(class_collection.find({}))
    highest_id = 0
    for item in class_list:
        highest_id = item['id'] if item['id'] > highest_id else highest_id
    result = class_collection.insert_one({ "id": highest_id + 1, "className": class_name, "weekday":class_weekday, "professor": class_professor,\
                                           "hour": class_hour, "color": class_color, "haveParticipantList": False }).inserted_id
    return f'{highest_id}' if result is not None else "Failed"

@app.route("/insertparticipantlist", methods=['POST'])
def insert_participant_list():
    class_id = request.json['id']
    participant_list = request.json['participantList']
    result = participant_collection.insert_one({"classId": class_id, "participantList": participant_list, "participantCounter": len(participant_list)}).inserted_id
    return "Success" if result is not None else "Failed"

@app.route("/getparticipantlist/<class_id>", methods=['GET'])
def get_participant_list(class_id):
    return list(participant_collection.find({"classId": int(class_id)}, {"_id": 0}))

@app.route("/openpresencelog", methods=['POST'])
def open_presence_log():
    class_id = request.json['id']
    date = request.json['date']
    participant_object = participant_collection.find_one({"classId": int(class_id)}, {"_id": 0})
    print(participant_object)
    if participant_object is None: 
        return "Nenhuma lista de participantes foi encontrada"
    presence_log = { "class_id": class_id, "window": True, "date": int(date), "presencePercentage": 0}
    for ra in participant_object['participantList']:
        presence_log[ra] = False
    result = presence_collection.insert_one(presence_log).inserted_id
    return "Success" if result is not None else 'Failed'