import chromadb.errors
from langchain_community.document_loaders import WebBaseLoader, PyPDFLoader, YoutubeLoader
from langchain_core.documents import Document

from langchain_groq import ChatGroq
# from langchain_community.vectorstores import Chroma
from langchain_chroma import Chroma
# from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import chromadb.utils.embedding_functions as embedding_functions

from langchain_community.utilities import WikipediaAPIWrapper
from langchain_community.tools import WikipediaQueryRun

from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
from pathlib import Path
import chromadb
import os
import requests
from uuid import uuid4 as v4

from typing import Literal


from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from utils.utils import RouteQuery
from typing import List
from typing_extensions import TypedDict

# from utils_.tiktok_util import transcribe
import time
import random


load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")


class RagApp():
    def __init__(self, num_documents_source=None, collection_name=None, online_pdfs=[], local_pdfs=[], web_urls=[], yt_urls=[], tiktok_urls=[]):
        # self.collection_name = "ragentic_chroma_google"
        self.collection_name = collection_name or str(v4())
        self.num_documents_source = num_documents_source or 4

        self.online_pdfs = online_pdfs
        self.local_pdfs = local_pdfs
        self.web_urls = web_urls
        self.yt_urls = yt_urls
        self.tiktok_urls = tiktok_urls

        self.data = []

    def get_chroma(self):
        SCRIPT_DIR = Path(__file__).parent
        self.client = chromadb.PersistentClient(path=str(SCRIPT_DIR / "db"))

    def get_embeddings(self):
        # self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        # self.embeddings = embedding_functions.HuggingFaceEmbeddingFunction(model_name="all-MiniLM-L6-v2", api_key=os.getenv("HF_TOKEN"))
        # self.embeddings = embedding_functions.GoogleGenerativeAiEmbeddingFunction(api_key=os.getenv("GOOGLE_API_KEY"))

    def web_loader(self):
        if not self.web_urls: return

        docs = [WebBaseLoader(url).load() for url in self.web_urls]
        docs_list = [item for sublist in docs for item in sublist]
        # print(len(docs))
        # print(len(docs[0]))
        # print(docs_list[0].metadata)

        self.data += docs_list

        

    def pdf_loader(self):
        data = []
        #Load local pdfs
        for pdf in self.local_pdfs:
            loader = PyPDFLoader(f"pdfs/{pdf}")
            data += loader.load()
        #     print(type(data))
        #     print(data[0])
        #     print("inner", len(data))
        # print(len(data))

        
        #Load online pdfs

        for url in self.online_pdfs:
            file_id = str(v4())
            file_name = file_id + ".pdf"
            response = requests.get(url)
            with open(file_name, 'wb') as f:
                f.write(response.content)
            loader = PyPDFLoader(file_name)
            data += loader.load()

        
            if os.path.exists(file_name):
                os.remove(file_name)

            print(type(data))
            print(data[0])
            print("inner", len(data))

       
            
        print(len(data))



        self.data += data
        
    
    def yt_loader(self):
        if not self.yt_urls: return
        data = []
        
        for url in self.yt_urls:
            loader = YoutubeLoader.from_youtube_url(
                url, add_video_info=False
            )
            data += loader.load()
        print(data)
        print("Yt loader", len(data))
        print(data[0])

        self.data += data

    def tiktok_loader(self):
        if not self.tiktok_urls: return
        # data = []
        # for url in self.tiktok_urls:
        #     duration, text = transcribe({"tiktokUrl": url})
        #     # time.sleep(random.randint(1, 5))
        #     data.append(Document(metadata={"source": url}, page_content=text))

        # print(data)
        # print("Tiktok loader", len(data))
        # print(data[0])

        # self.data += data




    def split_docs(self):

        self.web_loader()
        print("Total Data length:", len(self.data))
        self.pdf_loader()
        print("Total Data length:", len(self.data))
        self.yt_loader()
        print("Total Data length", len(self.data))
        self.tiktok_loader()
        print("Total Data length", len(self.data))

        text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            chunk_size=500, chunk_overlap=50
        )
        doc_splits = text_splitter.split_documents(self.data)
        

        doc_length = len(doc_splits)
        ids = [str(i) for i in range(doc_length)]
       
        return doc_splits
        # print(doc_splits[0].metadata)

    def create_vectorstore(self):

        try:
            collection = self.client.get_collection(name=self.collection_name)
            vector_store = Chroma(
                client=self.client,
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
            )

        except chromadb.errors.InvalidCollectionException:
            print(f"Creating collection: {self.collection_name}")
            # collection = self.client.create_collection(name="ragentic_chroma4", embedding_function=self.embeddings)
            # print(collection.count())
            # collection.upsert(
            #     documents=[doc.metadata["description"] for doc in doc_splits], 
            #     ids=ids,
            #     metadatas=[{"source": doc.metadata["source"], "title": doc.metadata["title"]} for doc in doc_splits]
            #     )
            
            # print(collection.count())
            # Add to vectorDB

            doc_splits = self.split_docs()
            vector_store = Chroma.from_documents(
                documents=doc_splits,
                collection_name=self.collection_name,
                embedding=self.embeddings,
                persist_directory="./db"
            )
            

        
       
        self.retriever = vector_store.as_retriever(search_kwargs={"k": self.num_documents_source})
        # result = self.retriever.invoke("what is an agent?")
        # print(result)
        # print(len(result))

    def create_question_router(self):
        llm = ChatGroq(groq_api_key=groq_api_key,model_name="Gemma2-9b-It")
        structured_llm_router = llm.with_structured_output(RouteQuery)

        system = """You are an expert at routing a user question to a vectorstore or the internet.
        The vectorstore contains documents related to agents, prompt engineering, adversarial attacks, traffic laws, marriage and bag shops.
        Use the vectorstore for questions on these topics. Otherwise, use internet."""
        route_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system),
                ("human", "{question}"),
            ]
        )

        self.question_router = route_prompt | structured_llm_router
        # self.question_router = route_prompt.pipe(structured_llm_router)
        # print(
        #     self.question_router.invoke(
        #         {"question": "what is agentic AI?"}
        #     ))
        
    def create_wiki(self):
        api_wrapper = WikipediaAPIWrapper(top_k_results=1,doc_content_chars_max=200)
        self.wiki = WikipediaQueryRun(api_wrapper=api_wrapper)
        # print(self.wiki.run("what is the capital city of India?"))

    def run(self):
        print("Loading embeddings")
        self.get_embeddings()
        print("Loading chromadb")
        self.get_chroma()
        print("Creating/Getting vectorstore")
        self.create_vectorstore()
        # print("Creating question router")
        # self.create_question_router()
        # print("Creating wiki")
        # self.create_wiki()







# app = RagApp()
# app.run()

