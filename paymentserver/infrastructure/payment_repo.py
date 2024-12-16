from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import certifi


uri = "mongodb+srv://shaylanger2:UvoeeZNb3HQ8Ijyn@cluster0.rd64v.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi("1"), tlsCAFile=certifi.where())

mydb = client["payments_db"]
payment_collection = mydb["payments"]
evidence_collection = mydb["evidence"]
