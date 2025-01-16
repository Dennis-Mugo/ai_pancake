from langgraph.graph import END, StateGraph, START
# from graph import GraphState, retrieve, wiki_search, route_question, generate
from graph import GraphState, Graph
from pprint import pprint

from IPython.display import Image, display


class WorkFlow:
    def __init__(self, num_documents_source=None, collection_name=None, online_pdfs=[], local_pdfs=[], web_urls=[], yt_urls=[], tiktok_urls=[], online_images=[]):
        
        self.graph = Graph(
            online_pdfs=online_pdfs,
            local_pdfs=local_pdfs,
            web_urls=web_urls,
            yt_urls=yt_urls,
            tiktok_urls=tiktok_urls,
            online_images=online_images,
            collection_name=collection_name,
            num_documents_source=num_documents_source
        )
        self.create_workflow()
        


    def create_workflow(self):
        workflow = StateGraph(GraphState)
        # Define the nodes
        # workflow.add_node("rag_llm_router", self.graph.rag_llm_router)  
        workflow.add_node("create_rag", self.graph.create_rag)  
        workflow.add_node("llm_image_search", self.graph.llm_image_search)  
        workflow.add_node("llm_text_search", self.graph.llm_text_search) 
        workflow.add_node("tiktok_download", self.graph.tiktok_download)
        workflow.add_node("retrieve", self.graph.retrieve) 
        workflow.add_node("generate", self.graph.generate) 

        # Build graph
        
        workflow.add_conditional_edges(
            START, 
            self.graph.rag_llm_router,
            {
                "create_rag": "create_rag",
                "llm_image_search": "llm_image_search",
                "llm_text_search": "llm_text_search",
                "tiktok_download": "tiktok_download"
            }
            )
        
        
        # Branch 1
        workflow.add_edge("create_rag", "retrieve")
        

        # Branch 2
        workflow.add_edge("llm_image_search", "llm_text_search")

        # Branch 3
        workflow.add_edge( "llm_text_search", END)

        workflow.add_edge("retrieve", "generate")
        workflow.add_edge("generate", END)

        # Branch 4
        workflow.add_edge("tiktok_download", END)

    

        # Compile
        self.flow = workflow.compile()

        self.draw_workflow()

    def draw_workflow(self):
        
        try:
            display(Image(self.app.get_graph().draw_mermaid_png()))
        except Exception:
            print("Flow could not be displayed!")

    def stream(self, question):
        inputs = {
            "question": question
        }
        for output in self.flow.stream(inputs):
            for key, value in output.items():
                # Node
                pprint(f"Node '{key}':")
                # Optional: print full state at each node
                # pprint(value["keys"], indent=2, width=80, depth=None)
            # pprint("\n---\n")

        # Final generation
        # pprint(value['documents'][0].dict()['metadata']['description'])

        # pprint(value['generation'])
        print('-----------------------------------------------------------')
        print(value["generation"])
        # print(value)
        
        return {
            "documents": [doc.dict() for doc in value["documents"]],
            "numDocuments": len(value["documents"]),
            "generation": value["generation"],
            "question": value["question"]
        }
    

# flow = WorkFlow()
# result = flow.stream("what is agentic AI?")
# print("---------------------FINAL RESULT------------------------")
# print(result.keys())