import importlib.util
import sys
from uuid import uuid4 as v4
import time
from firebase_config.config import db



def addUserChatToDatabase(userId, conversationId, userObj):
    
    chat_id = str(v4())

    # db = firebase_config.db
    db.document(f"users/{userId}/conversations/{conversationId}/chats/{chat_id}").set({
        "dateCreated": userObj["dateCreated"],
        "role": userObj["role"],
        "prompt": userObj["prompt"],
    })


def addUserChatToDatabase_w(userId, obj):
    
    obj["dateCreated"] = str(int(time.time() * 1000))
    obj["role"] = "user"

    new_user = True
    user_ref = db.document(f"ai_pancake_users/{userId}")
    if user_ref.get().exists: 
        new_user = False
    else:
        user_ref.set({
            "dateCreated": str(int(time.time() * 1000)),
            "profileName": obj["ProfileName"],
        })
        
    chat_id = str(v4())
        

    db.document(f"ai_pancake_users/{userId}/chats/{chat_id}").set(obj)

    return new_user

    


def addAssistantChatToDatabase(userId, conversationId, assistantObj):
    chat_id = str(v4())
    db.document(f"users/{userId}/conversations/{conversationId}/chats/{chat_id}").set({
        "dateCreated": str(int(time.time() * 1000)),
        "role": "assistant",
        "content": assistantObj["answer"],
        "sourceDocuments": assistantObj["sourceDocuments"],
    })


def addAssistantChatToDatabase_w(userId, assistantObj):
    assistantObj["dateCreated"] = str(int(time.time() * 1000))
    assistantObj["role"] = "assistant"
    chat_id = str(v4())
    db.document(f"ai_pancake_users/{userId}/chats/{chat_id}").set(assistantObj)