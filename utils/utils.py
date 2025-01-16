from typing import Literal

import os
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from firebase_config.config import bucket

from uuid import uuid4 as v4
from urllib.parse import urlparse

class RouteQuery(BaseModel):
    """Route a user query to the most relevant datasource."""

    datasource: Literal["vectorstore", "internet"] = Field(
        ...,
        description="Given a user question choose to route it to internet or a vectorstore.",
    )


accepted_message_types = [
    "text",
    "image",
    "document"
]

accepted_media_types = [
    "application/pdf",
    "image/jpeg",
    "image/png"
]

def validate_message(message_type, media_type):
    if message_type == "text":
        return "", True
    
    if message_type not in accepted_message_types:
        return f"Sorry, the message is not supported 😔", False
    
    if media_type not in accepted_media_types:
        return f"Sorry, the message is not supported 😔", False
    
    return "", True
    

def is_banned_user(user_id):
    #banned_users = ["254742063263", "254723068001"]
    banned_users = []
    message = False
    if user_id not in banned_users:
      return False

    message = "You are banned from using this service 😔"
    return message


def download_video(url=None):
    import pyktok as pyk
    # tiktok_url = 'https://www.tiktok.com/@username/video/1234567890'
    # tiktok_url = 'https://www.tiktok.com/@emmanuellord2/video/7426309007268171013'
    # tiktok_url = 'https://www.tiktok.com/@mr.handsome049/video/7431195909347888430'
    # tiktok_url="https://www.tiktok.com/@endlessmomdiary/video/7457563613318958354?is_from_webapp=1&sender_device=pc"
    # tiktok_url = "https://www.tiktok.com/@alpha_ridesmombasa/video/7391795734082800902?is_from_webapp=1&sender_device=pc"
    # tiktok_url = "https://www.tiktok.com/@dingaworldltd/video/7326073303083322629?is_from_webapp=1&sender_device=pc"
    tiktok_url = url or "https://www.tiktok.com/@denriafrica/video/7399252159436557573?is_from_webapp=1&sender_device=pc"


    tiktok_url = tiktok_url.split("?")[0]
    pyk.save_tiktok(video_url=tiktok_url,
                save_video=True,
                metadata_fn='',
                browser_name=None,
                return_fns=False
		)
    
    if tiktok_url[:10] == "https://vm":
        lst =tiktok_url.split("/")
        lst = [i for i in lst if i != ""]
        video_name = lst[-1] + "_.mp4"
    else:
        video_name = tiktok_url[23:] + ".mp4"
        video_name = video_name.replace("/", "_")
    
    
    return video_name

def upload_file(path):
    print(">>> Uploading video")
    
    blob = bucket.blob(f'ai_pancake/{str(v4())}')
    blob.upload_from_filename(path)
    blob.make_public()
    url = blob.public_url
    
    if os.path.exists(path):
        os.remove(path)
    return url

def get_tiktok_video_url(url):
    try:
        download_name = download_video(url)
        print(download_name)
        new_url = upload_file(download_name)
        print(new_url)
        return new_url
    except Exception as e:
        print(str(e))
        return None
    

def is_valid_link(string):
    try:
        result = urlparse(string)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


    

