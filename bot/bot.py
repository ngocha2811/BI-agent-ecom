import json
from dotenv import load_dotenv
from openai import OpenAI
from bot.tools import TOOLS, save_memory, search_web, invoke_model, get_data_df_local
# create_notion_page


load_dotenv()

def bot(messages):

    # Initialize the OpenAI client
    client = OpenAI()

    # Make a ChatGPT API call with tool calling
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        tools=TOOLS, # here we pass the tools to the LLM
        messages=messages
    )

    # Get the response from the LLM
    response = completion.choices[0].message

    messages.append(response)

    if response.tool_calls:
        for tool_call in response.tool_calls:
            tool_call_arguments = json.loads(tool_call.function.arguments)
            if tool_call.function.name == "save_memory":
                result = save_memory(tool_call_arguments["memory"])
                messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result})
            elif tool_call.function.name == "web_search":
                search_results = search_web(tool_call_arguments["query"])
                messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": f"Here are the search results: {search_results}"})
            elif tool_call.function.name == "get_data_df":
                result = get_data_df_local(tool_call_arguments["sql_query"])
                messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result})
            # elif tool_call.function.name == "create_notion_page":
            #     result = create_notion_page(tool_call_arguments["page_title"], tool_call_arguments["markdown_content"])
            #     messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result})
        return invoke_model(messages)
    else:
        return response.content