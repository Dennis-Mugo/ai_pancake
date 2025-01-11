import os
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from dotenv import load_dotenv
import requests

load_dotenv()

# Find your Account SID and Auth Token at twilio.com/console
# and set the environment variables. See http://twil.io/secure
account_sid = os.getenv("SID")
auth_token = os.getenv("AUTH_TOKEN")
try:
    client = Client(account_sid, auth_token)

    # print(account_sid)
    # print(auth_token)

except TwilioRestException as e:
    print(e.msg)


def format_twilio_url(actual_url):
    sample = "https://username:password@api.twilio.com/2010-04-01/your_desired_path"
    # actual_url = "https://api.twilio.com/2010-04-01/Accounts/AC0c0f918ec0664863d6ee499b521c16ca/Messages/MM7602b24db1226f74c95d46e3987d3ac0/Media/ME5645af977f30a31a62b96ec639fc7ae4"

    length = len("https://")
    url = f"https://{account_sid}:{auth_token}@{actual_url[length:]}"
    return url

def get_image(url):
    response = requests.get(url)
    print(response.content)
    return response.content


def format_text(text):
    result = ""
    i = 0
    while i < len(text):
        char = text[i]
        if char == "*":
            result += "*"
            i += 1
            while i < len(text) and text[i] == "*":
                i += 1
        else:
            result += char
            i += 1
    return result

def split_long_message(text):
    limit = 1500
    messages = []
    counter = 0
    curr_message = ""
    while counter < len(text):
        curr_message = text[counter:counter+limit]
        messages.append(curr_message)
        counter += limit
    return messages

def send_multiple_messages(body, to, from_="whatsapp:+12314325850"):
    formatted = format_text(body)
    messages = split_long_message(formatted)
    for message in messages:
        try:
            message = client.messages.create(
                body=message,
                from_=from_,
                to=f"whatsapp:+{to}",
            )
            message = message.__dict__

        except TwilioRestException as e:
            print(e.msg)
            return {"error": e.msg, "messages": []}
        # for key in message:
        #     print(f"{key}: {message[key]}")
    return {
            "error": False,
            "messages" : [len(message) for message in messages]
        }





