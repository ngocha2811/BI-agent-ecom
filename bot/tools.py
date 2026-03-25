import os
import uuid
import pandas as pd
from datetime import datetime, timezone
from pinecone import Pinecone
from openai import OpenAI
from tavily import TavilyClient
from sqlalchemy import text
from ai.utils import connect_to_local_database
#from notion_client import Client
from dotenv import load_dotenv
#from notion_functions import add_markdown_to_notion


load_dotenv()

# Initialize Pinecone for vector database
pc = Pinecone(os.getenv("PINECONE_API_KEY"))
# Initialize the vector database index
index = pc.Index(os.getenv("PINECONE_INDEX_NAME"))
# Initialize OpenAI for embeddings 
client = OpenAI()

# Define the tools
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "save_memory",
            "description": "Save a memory to the vector database",
            "parameters": {
                "type": "object",
                "properties": {
                    "memory": {"type": "string"}
                },
                "required": ["memory"]
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for information",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_data_df",
            "description": (
                "Execute a PostgreSQL SELECT query against the e-commerce database and "
                "return the results as a table. Use this for any question that requires "
                "data — sales, revenue, products, ads, margins, etc."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "sql_query": {
                        "type": "string",
                        "description": "A valid PostgreSQL SELECT statement to run against the database.",
                    }
                },
                "required": ["sql_query"],
            },
        },
    },
    # {
    #     "type": "function",
    #     "function": {
    #         "name": "create_notion_page",
    #         "description": "Create a new page in Notion",
    #         "parameters": {
    #             "type": "object",
    #             "properties": {
    #                 "page_title": {"type": "string"},
    #                 "markdown_content": {"type": "string"}
    #             },
    #             "required": ["page_title", "markdown_content"]
    #         },
    #     },
    # },
]

# Function to get the embeddings of a string
def get_embeddings(string_to_embed):
    response = client.embeddings.create(
        input=string_to_embed,
        model=os.getenv("EMBEDDING_MODEL"),
        dimensions=int(os.getenv("EMBEDDING_DIMENSIONS"))
    )
    return response.data[0].embedding

def save_memory(memory):
    # Step 1: Embed the memory
    vector = get_embeddings(memory)
    # Step 2: Build the vector document to be stored
    user_id = "1234"
    current_time = datetime.now(tz=timezone.utc)
    documents = [
        {
            "id": str(uuid.uuid4()),
            "values": vector,
            "metadata": {
                "user_id": user_id,
                "timestamp": str(current_time),
                "payload": memory,
            },
        }
    ]
    # Step 3: Store the vector document in the vector database
    index.upsert(
        vectors=documents,
        namespace=os.getenv("PINECONE_NAMESPACE")
    )
    return "Memory saved successfully"

def load_memories(prompt):
    user_id = "1234"
    top_k = 3
    vector = get_embeddings(prompt)
    response = index.query(
        vector=vector,
        filter={
            "user_id": {"$eq": user_id},
        },
        namespace=os.getenv("PINECONE_NAMESPACE"),
        include_metadata=True,
        top_k=top_k,
    )
    memories = []
    if matches := response.get("matches"):
        memories = [m["metadata"]["payload"] for m in matches]
    return memories

def search_web(query):
    # Initialize Tavily
    tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    return "\n".join(f"{{Content: {result['content']} \n Source: {result['url']}}}" for result in tavily.search(query, search_depth="basic")["results"])

def get_data_df_local(sql_query: str) -> str:
    """Execute a SQL query and return results as formatted text for Telegram."""
    try:
        conn = connect_to_local_database()
        result = conn.execute(text(sql_query))
        rows = result.all()
        columns = list(result.keys())
        conn.close()
    except Exception as e:
        return f"Query failed: {e}"

    if not rows:
        return "No data found for this query."

    df = pd.DataFrame(rows, columns=columns)
    preview = df.head(20).to_string(index=False)
    suffix = f"\n_(showing 20 of {len(df)} rows)_" if len(df) > 20 else f"\n_{len(df)} row(s) returned._"
    return f"```\n{preview}\n```{suffix}"


def invoke_model(messages):
    # Initialize the OpenAI client
    client = OpenAI()

    # Make a ChatGPT API call with tool calling
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )

    return completion.choices[0].message.content

# def create_notion_page(page_title, markdown_content):

#     # Initialize Notion client
#     notion = Client(auth=os.getenv("NOTION_API_KEY"))
#     NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

#     # Create a new page
#     page = notion.pages.create(
#         parent={"database_id": NOTION_DATABASE_ID},
#         properties={"title": {"title": [{"text": {"content": page_title}}]}}
#     )
#     print(page)
#     # Add the markdown text to the page
#     add_markdown_to_notion(page["id"], markdown_content)
#     return "Page created successfully"

