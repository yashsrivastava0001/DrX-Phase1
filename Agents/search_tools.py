from typing import Literal
from openai import AsyncOpenAI
from autogen_core.tools import FunctionTool
import os

# Initialize client later when we have the API key
client = None


def initialize_client(api_key):
    global client
    client = AsyncOpenAI(api_key=api_key)


async def web_search_tool(
        query: str,
        depth: Literal["low", "medium", "high"] = "high"
) -> str:
    """Run OpenAI hosted web search and return a cited summary (optionally deeper)."""
    resp = await client.responses.create(
        model="gpt-5",
        input=f"Search the web for: {query}. Summarize with dates and include citations. "
              f"Return JSON with fields: summary, sources[{'{title,url,date}'}].",
        tools=[{"type": "web_search", "search_context_size": depth}],
        tool_choice="auto",
    )
    return resp.output_text


async def g4o_search_tool(
        query: str,
        search_context_size: str = "high",
        country: str = None, city: str = None, region: str = None, timezone: str = None
) -> str:
    web_search_options = {"search_context_size": search_context_size}
    if any([country, city, region, timezone]):
        web_search_options["user_location"] = {
            "type": "approximate",
            "approximate": {
                **({"country": country} if country else {}),
                **({"city": city} if city else {}),
                **({"region": region} if region else {}),
                **({"timezone": timezone} if timezone else {}),
            }
        }

    comp = await client.chat.completions.create(
        model="gpt-4o-search-preview",
        messages=[
            {"role": "system", "content": "Be concise. Include URLs and dates as citations."},
            {"role": "user", "content": query},
        ],
        extra_body={"web_search_options": web_search_options},
    )
    return comp.choices[0].message.content


g4o_search_fn = FunctionTool(
    g4o_search_tool,
    description="Search the web (GPT-4o Search Preview) and return a concise, cited summary.",
    name="g4o_search_tool",
)

web_search_fn = FunctionTool(
    web_search_tool,
    description="Run OpenAI hosted web search and return a dated, cited summary.",
    name="web_search_tool",
)


def google_search(query: str):
    """
    Performs a Google search using the Custom Search JSON API.

    Parameters:
        query (str): Search query string.

    Returns:
        list: A list of dictionaries containing title, link, and snippet.
    """
    cse_id = "b4d3e101dea6543c2"
    # Implementation follows...
    pass