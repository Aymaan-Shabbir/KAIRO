from langchain.tools import tool
import requests
from bs4 import BeautifulSoup
from tavily import TavilyClient
import os
from dotenv import load_dotenv
load_dotenv()
from rich import print

tavily = TavilyClient(api_key= os.getenv("TAVILY_API_KEY"))


@tool
def web_search(query:str) -> str:
    """Search the web for recent and reliable information on a topic. returns Titles, URLs and snippets"""
    results = tavily.search(query=query, max_results=3)
    out = []
    for r in results['results']:
        out.append(
         f"Title : {r.get('title', 'N/A')}\n"
         f"URL : {r.get('url', 'N/A')}\n"
         f"Snippet : {r.get('content', 'N/A')}\n"
        )
    return "\n---\n".join(out)




@tool
def scrape_url(url: str) -> str:
    """Scrape and return clean text content from a given URL for deeper reading."""

    try:
        # Send an HTTP GET request to the website and wait for a maximum of 8 seconds
        # User-Agent makes the request look like it comes from a browser
        resp = requests.get(
            url,
            timeout=8,
            headers={"User-Agent": "Mozilla/5.0"}
        )

        # Parse the website's HTML into a structured BeautifulSoup object
        soup = BeautifulSoup(resp.text, "html.parser")

        # Find unwanted HTML tags such as scripts, styles, navigation, and footer
        for tag in soup(["script", "style", "nav", "footer"]):

            # Completely remove each matching tag and its contents
            tag.decompose()

        # Extract clean text, separate text chunks with spaces,
        # remove extra whitespace, and keep only the first 3000 characters
        return soup.get_text(separator=" ", strip=True)[:3000]

    except Exception as e:
        # If an error occurs, return a message describing the error
        return f"Could not scrape URL: {str(e)}"


