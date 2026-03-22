import json
import os
from dotenv import load_dotenv
from openai import OpenAI
from ai.tools import get_data_df_local, create_chart_local, TOOLS

load_dotenv()

# Rows sent to Grok for interpretation — capped to avoid token overload
_MAX_INSIGHT_ROWS = 20


def _get_insight(client, df) -> str:
    """Make a plain-text Grok call to interpret a DataFrame result."""
    preview = df.head(_MAX_INSIGHT_ROWS).to_string(index=False)
    insight_completion = client.chat.completions.create(
        model="grok-3-mini",
        messages=[
            {
                "role": "user",
                "content": (
                    f"Here are the query results:\n\n{preview}\n\n"
                    "Please write a 2-3 sentence business insight interpreting this data."
                ),
            }
        ],
    )
    return insight_completion.choices[0].message.content


def agent(messages):
    client = OpenAI(
        api_key=os.environ["XAI_API_KEY"],
        base_url="https://api.x.ai/v1",
    )

    completion = client.chat.completions.create(
        model="grok-3-mini",
        tools=TOOLS,
        messages=messages,
    )

    response = completion.choices[0].message

    if response.tool_calls:
        for tool_call in response.tool_calls:
            args = json.loads(tool_call.function.arguments)
            name = tool_call.function.name

            if name == "get_data_df":
                df, status = get_data_df_local(args["sql_query"])

            elif name == "create_chart":
                df, status = create_chart_local(
                    sql_query=args["sql_query"],
                    chart_type=args["chart_type"],
                    x_column=args["x_column"],
                    y_column=args["y_column"],
                    title=args["title"],
                )
            else:
                return f"Unknown tool: {name}"

            # df is None when query failed or returned no rows
            if df is None:
                return status

            return _get_insight(client, df)

    else:
        return response.content