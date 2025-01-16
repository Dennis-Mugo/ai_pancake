from typing import List

from typing_extensions import TypedDict
from rag import RagApp
from langchain.schema import Document

from langchain_groq import ChatGroq

from prompts import prompt_template

from langchain import hub
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
import os

from utils.utils import is_valid_link, get_tiktok_video_url

load_dotenv()

groq_api_key = os.getenv("GROQ_API_KEY")
langsmith_api_key = os.getenv("LANGSMITH_API_KEY")

import easyocr
import requests
image_reader = easyocr.Reader(['en', 'es', 'de'], gpu=True)



class GraphState(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        question: question
        generation: LLM generation
        documents: list of documents
    """

    question: str
    generation: str
    documents: List[str]
    

class Graph:
    def __init__(self, num_documents_source=None, collection_name="", online_pdfs=[], local_pdfs=[], web_urls=[], yt_urls=[], tiktok_urls=[], online_images=[]):

        
        self.online_pdfs = online_pdfs,
        self.local_pdfs = local_pdfs,
        self.web_urls = web_urls,
        self.yt_urls = yt_urls,
        self.tiktok_urls = tiktok_urls,
        self.online_images = online_images,
        self.collection_name = collection_name,
        self.num_documents_source = num_documents_source

        

    def rag_llm_router(self, state: GraphState):
        print("---RAG LLM ROUTER---")
        print(self.__dict__)

        question = state["question"]

        if is_valid_link(question) and ("https://vm.tiktok.com" in question or "https://www.tiktok.com" in question):
            return "tiktok_download"

        elif self.online_pdfs[0]:
            
            return "create_rag"
        elif self.online_images[0]:
           
            return "llm_image_search"
        else:
            
            return "llm_text_search"
        
    def create_rag(self, state: GraphState):
        print("---CREATE RAG---")
        self.app = RagApp(
            online_pdfs = self.online_pdfs[0],
            local_pdfs = self.local_pdfs[0],
            web_urls = self.web_urls[0],
            yt_urls = self.yt_urls[0],
            tiktok_urls = self.tiktok_urls[0],
            collection_name = self.collection_name[0],
            num_documents_source = self.num_documents_source
        )
        print(self.app.__dict__)
        self.app.run()
        return {"documents": [], "question": state["question"],  "generation": ""}
    
    def llm_image_search(self, state: GraphState):
        print("---LLM IMAGE SEARCH---")
        print(self.online_images[0][0])
        # text = image_reader.readtext(self.online_images[0][0])

        res = requests.get(self.online_images[0][0])
        text = ""
        text = image_reader.readtext(res.content)

        if len(text) == 0:
            return {"documents": [], "question": "tell the user that no text could be found in the image",  "generation": ""}
        lines = [f"{item[1]}" for item in text]
        text = "/n".join(lines)
        new_question = text + "\n\n" + state["question"]
        return {"documents": [], "question": new_question,  "generation": ""}

        
    def llm_text_search(self, state: GraphState):
        print("---LLM SEARCH---")
        messages = [
            (
                "system",
                "You are a helpful assistant. Ensure your responses are well-formatted by using break lines, lists and bold texts for titles and emphasis. Use emojis for non-serious responses.",
            ),
            ("human", state["question"]),
        ]
        llm = ChatGroq(groq_api_key=groq_api_key,model_name="llama3-70b-8192")
        answer = llm.invoke(messages)
        return {"documents": [], "question": state["question"],  "generation": answer.content}
    
    def tiktok_download(self, state: GraphState):
        print("---TIKTOK DOWNLOAD---")

        url = state["question"]
        new_url = get_tiktok_video_url(url)
        if new_url["link"]:
            return {"documents": [], "question": state["question"],  "generation": new_url}
        
        return {"documents": [], "question": state["question"],  "generation": new_url["error"]}

    def retrieve(self, state: GraphState):
        """
        Retrieve documents

        Args:
            state (dict): The current graph state

        Returns:
            state (dict): New key added to state, documents, that contains retrieved documents
        """
        print("---RETRIEVE---")
        question = state["question"]

        # Retrieval
        documents = self.app.retriever.invoke(question)
        return {"documents": documents, "question": question, "generation": ""}

    def wiki_search(self, state):
        """
        wiki search based on the re-phrased question.

        Args:
            state (dict): The current graph state

        Returns:
            state (dict): Updates documents key with appended web results
        """

        print("---wikipedia---")
        print("---HELLO--")
        question = state["question"]
        print(question)

        # Wiki search
        docs = self.app.wiki.invoke({"query": question})
        #print(docs["summary"])
        wiki_results = docs
        wiki_results = Document(page_content=wiki_results)

        return {"documents": [wiki_results], "question": question,  "generation": ""}
    


    def route_question(self, state):
        """
        Route question to internet search or RAG.

        Args:
            state (dict): The current graph state

        Returns:
            str: Next node to call
        """

        print("---ROUTE QUESTION---")
        return "vectorstore"
        question = state["question"]
        source = self.app.question_router.invoke({"question": question})
        if source.datasource == "internet":
            print("---ROUTE QUESTION TO LLM SEARCH---")
            return "internet"
        elif source.datasource == "vectorstore":
            print("---ROUTE QUESTION TO RAG---")
            return "vectorstore"
        
    def generate(self, state):
        """
        Generate answer based on the retrieved documents and the question.
        
        Args:
            state (dict): The current graph state
        
        Returns:
            state (dict): Updates generation key with the generated answer
        """
        print("---GENERATE---")
        
    #   os.environ["LANGCHAIN_API_KEY"] = langsmith_key
    #   os.environ["LANGCHAIN_TRACING_V2"]="true"
    #   os.environ["LANGCHAIN_PROJECT"]="Langgraph"


        prompt = PromptTemplate(
            template=prompt_template, input_variables=["context", "question"]
        )
        # prompt = hub.pull("rlm/rag-prompt")


        llm = ChatGroq(groq_api_key=groq_api_key, model_name="llama3-70b-8192")
        rag_chain = prompt | llm | StrOutputParser()
        response = rag_chain.invoke({"context": state["documents"], "question": state["question"]})
        # print(response)
        return {"documents": state["documents"], "question": state["question"],  "generation": response}

    
