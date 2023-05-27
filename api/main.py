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
                                           "hour": class_hour, "color": class_color}).inserted_id
    return f'{highest_id}' if result is not None else "Failed"

