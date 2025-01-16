from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import random
from twilio_util.main import send_multiple_messages, send_message, format_twilio_url
from utils.utils import validate_message, is_banned_user, is_valid_link
from utils.database import addUserChatToDatabase_w, addAssistantChatToDatabase_w
from flow import WorkFlow


app = Flask(__name__)
CORS(app)

response_format = {
    "data": {},
    "errors": [],
    "status": 200
}






def hello():
    res = response_format.copy()
    res["data"] = {"hello": "world"}
    return jsonify(res)

def prompt():
    res = response_format.copy()
    body = request.form.to_dict()
    print(body)
    
    # for key in body:
    #     print(f"{key}: {body[key]}")

    question = body.get("Body", False)
    user_id = body.get("WaId", False)
    message_id = body.get("MessageSid", False)
    profile_name = body.get("ProfileName", False)
    message_type = body.get("MessageType", False)
    media_type = body.get("MediaContentType0", "")
    media_url = body.get("MediaUrl0", "")

   

    addUserChatToDatabase_w(user_id, body)

    

    user_banned = is_banned_user(user_id)
    if user_banned:
        send_multiple_messages(body=user_banned, to=user_id)
        res["data"] = {"message": user_banned}
        addAssistantChatToDatabase_w(user_id, res["data"])
        return jsonify(res)
    
    error_message, is_valid = validate_message(message_type, media_type)
    if not is_valid: 
        send_multiple_messages(body=error_message, to=user_id)
        res["data"] = {"message": error_message}
        addAssistantChatToDatabase_w(user_id, res["data"])
        return jsonify(res)
    
    online_pdfs, online_images = [], []
    if media_type == "application/pdf":
        media_url = format_twilio_url(media_url)
        online_pdfs = [media_url]

    if message_type == "image":
        media_url = format_twilio_url(media_url)
        online_images = [media_url]
    
    num_documents_source = body.get("numDocumentsSource", "")

    # send_multiple_messages(body="Thinking...", to=user_id)

    
    if not question and not online_images and not online_pdfs:
        print("Error: No question provided")
        res["errors"].append("No question provided")
        res["status"] = 400
        addAssistantChatToDatabase_w(user_id, {"message": "No question provided"})
        return jsonify(res)
    
    
    try:
        flow = WorkFlow(
            online_pdfs = online_pdfs,
            online_images = online_images,
            local_pdfs = [],
            web_urls = [],
            yt_urls = [],
            tiktok_urls = [],
            collection_name = "",
            num_documents_source = 4
            
        )
        result = flow.stream(question)
        res["data"] = result
        print(result)
        addAssistantChatToDatabase_w(user_id, result)

        if is_valid_link(result["generation"]):
            send_message(body="Here is your downloaded video😊", to=user_id, media_url=[result["generation"]])
        else:
            send_multiple_messages(body=result["generation"], to=user_id)

    except Exception as e:
        print(e)
        # response["errors"].append("An error occured!")
        res["errors"].append(str(e))
        res["status"] = 500
        addAssistantChatToDatabase_w(user_id, {"message": str(e)})
        send_multiple_messages(body="An error occured!", to=user_id)

    return jsonify(res)
    


app.add_url_rule("/", "hello", hello, methods=["GET"])
app.add_url_rule("/prompt", "prompt", prompt, methods=["POST"])


if __name__=='__main__':
    app.run(host="0.0.0.0", port="8080", debug=False)
