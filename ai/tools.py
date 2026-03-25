import streamlit as st
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv
from .utils import connect_to_local_database
from sqlalchemy import text

load_dotenv()

TOOLS = [
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
    {
        "type": "function",
        "function": {
            "name": "create_chart",
            "description": (
                "Execute a PostgreSQL SELECT query and render the results as an interactive chart. "
                "Use this when the user asks for a chart, graph, plot, or visual. "
                "Supported chart types: bar, line, area, scatter, pie."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "sql_query": {
                        "type": "string",
                        "description": "A valid PostgreSQL SELECT statement. The first column becomes the x-axis / labels, subsequent numeric columns become the values.",
                    },
                    "chart_type": {
                        "type": "string",
                        "enum": ["bar", "line", "area", "scatter", "pie"],
                        "description": "The type of chart to render.",
                    },
                    "x_column": {
                        "type": "string",
                        "description": "The column name to use for the x-axis (or labels for pie charts).",
                    },
                    "y_column": {
                        "type": "string",
                        "description": "The column name to use for the y-axis (or values for pie charts).",
                    },
                    "title": {
                        "type": "string",
                        "description": "A short descriptive title for the chart.",
                    },
                },
                "required": ["sql_query", "chart_type", "x_column", "y_column", "title"],
            },
        },
    },
]


def get_data_df_local(sql_query: str) -> tuple[pd.DataFrame | None, str]:
    """Execute query, render the table, and return (df, status_message)."""
    try:
        conn = connect_to_local_database()
        result = conn.execute(text(sql_query))
        rows = result.all()
        columns = list(result.keys())
        conn.close()
    except Exception as e:
        st.error(f"Database error: {e}")
        return None, f"Query failed: {e}"

    if not rows:
        st.info("The query returned no results.")
        return None, "No data found for this query."

    df = pd.DataFrame(rows, columns=columns)
    with st.expander("SQL Query", expanded=False):
        st.code(sql_query, language="sql")
    st.dataframe(df, width="stretch")
    return df, f"Query returned {len(df)} row(s)."


def create_chart_local(sql_query: str, chart_type: str, x_column: str, y_column: str, title: str) -> tuple[pd.DataFrame | None, str]:
    """Execute query, render the chart, and return (df, status_message)."""
    try:
        conn = connect_to_local_database()
        result = conn.execute(text(sql_query))
        rows = result.all()
        columns = list(result.keys())
        conn.close()
    except Exception as e:
        st.error(f"Database error: {e}")
        return None, f"Query failed: {e}"

    if not rows:
        st.info("The query returned no results — nothing to chart.")
        return None, "No data found for this query."

    df = pd.DataFrame(rows, columns=columns)

    if x_column not in df.columns or y_column not in df.columns:
        st.error(f"Column not found. Available columns: {list(df.columns)}")
        return None, f"Chart failed: column '{x_column}' or '{y_column}' not in query results."

    try:
        if chart_type == "bar":
            fig = px.bar(df, x=x_column, y=y_column, title=title, text_auto=True)
        elif chart_type == "line":
            fig = px.line(df, x=x_column, y=y_column, title=title, markers=True)
        elif chart_type == "area":
            fig = px.area(df, x=x_column, y=y_column, title=title)
        elif chart_type == "scatter":
            fig = px.scatter(df, x=x_column, y=y_column, title=title)
        elif chart_type == "pie":
            fig = px.pie(df, names=x_column, values=y_column, title=title)
        else:
            st.error(f"Unknown chart type: {chart_type}")
            return None, f"Unknown chart type: {chart_type}"

        fig.update_layout(xaxis_tickangle=-35)
        with st.expander("SQL Query", expanded=False):
            st.code(sql_query, language="sql")
        st.plotly_chart(fig, width="stretch")
        return df, f"{chart_type.capitalize()} chart rendered with {len(df)} data points."

    except Exception as e:
        st.error(f"Chart error: {e}")
        return None, f"Chart failed: {e}"



