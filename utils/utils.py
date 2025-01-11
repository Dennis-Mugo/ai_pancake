from typing import Literal


from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field


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
    

    