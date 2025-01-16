import firebase_admin
from firebase_admin import credentials, storage, firestore, auth

cred = credentials.Certificate("firebase_config/private.json")
# cred = credentials.Certificate("private.json")
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred, {'storageBucket': 'sheriai.appspot.com'})

bucket = storage.bucket()
db = firestore.client()

# import firebase_admin
# from firebase_admin import credentials, storage, firestore, auth



# cred = credentials.Certificate("firebase_config/credentials.json")
# firebase_admin.initialize_app(cred, {'storageBucket': 'chatify--chat.appspot.com'})

# bucket = storage.bucket()
# db = firestore.client()