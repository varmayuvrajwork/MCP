from mcp.server.fastmcp import FastMCP
import requests
from openai import AzureOpenAI
import json
import os
from typing import List, Dict, Any, Optional
import re
from bs4 import BeautifulSoup
from dotenv import load_dotenv
load_dotenv()

mcp = FastMCP("EnhancedKnowledgeAssistant")

AZURE_API_KEY = os.getenv("AZURE_OPENAI_KEY")
AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_DEPLOYMENT_NAME = os.getenv("AZURE_DEPLOYMENT_NAME", "gpt-4o")
llm = AzureOpenAI(
      azure_endpoint=AZURE_ENDPOINT,
      api_key=AZURE_API_KEY,  
      azure_deployment=AZURE_DEPLOYMENT_NAME,
      api_version="2024-12-01-preview"
)

@mcp.tool()
def search_google(query: str, num_results: int = 3) -> str:
      """Search the web using Google Custom Search API.
      
      Args:
            query: Search query
            num_results: Number of results (1-10)
      """
      api_key = os.environ.get("GOOGLE_API_KEY")
      search_engine_id = os.environ.get("GOOGLE_CSE_ID")
      
      if not api_key or not search_engine_id:
            return "Error: Google Search API key or Search Engine ID not configured."
      
      url = "https://www.googleapis.com/customsearch/v1"
      params = {
            "key": api_key,
            "cx": search_engine_id,
            "q": query,
            "num": min(max(1, num_results), 10)
      }
      
      try:
            response = requests.get(url, params=params)
            results = response.json()
            
            if "items" not in results:
                  return f"No results found for query: {query}"
            
            formatted_results = []
            for item in results["items"]:
                  formatted_results.append(
                  f"Title: {item['title']}\n"
                  f"Link: {item['link']}\n"
                  f"Snippet: {item['snippet']}\n"
                  )
            
            return "\n\n".join(formatted_results)
            
      except Exception as e:
            return f"Error performing Google search: {str(e)}"

@mcp.tool()
def get_webpage_content(url: str, max_length: int = 3000) -> str:
      """Fetch and extract the main content from a webpage.
      
      Args:
            url: The URL of the webpage to fetch
            max_length: Maximum content length to return
      
      Returns:
            Extracted text content from the webpage
      """
      try:
            headers = {
                  "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Parse HTML content
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script_or_style in soup(["script", "style", "header", "footer", "nav"]):
                  script_or_style.decompose()
            
            # Get text content
            text = soup.get_text(separator='\n')
            
            # Clean up text (remove excessive newlines, etc.)
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            # Limit length
            if len(text) > max_length:
                  text = text[:max_length] + "... [content truncated]"
            
            return text
      except Exception as e:
            return f"Error fetching webpage content: {str(e)}"

@mcp.tool()
def search_serper(query: str, num_results: int = 3) -> str:
      """Search the web using Serper.dev API (Google results).
      
      Args:
            query: Search query
            num_results: Number of results (1-10)
      """
      api_key = os.environ.get("SERPER_API_KEY")
      
      if not api_key:
            return "Error: Serper API key not configured."
      
      url = "https://google.serper.dev/search"
      payload = {
            "q": query,
            "num": min(max(1, num_results), 10)
      }
      headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json"
      }
      
      try:
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            results = response.json()
            
            if "organic" not in results:
                  return f"No results found for query: {query}"
            
            formatted_results = []
            for item in results["organic"][:num_results]:
                  formatted_results.append(
                  f"Title: {item['title']}\n"
                  f"Link: {item['link']}\n"
                  f"Snippet: {item.get('snippet', 'No snippet available')}\n"
                  )
            
            return "\n\n".join(formatted_results)
            
      except Exception as e:
            return f"Error performing Serper search: {str(e)}"

@mcp.tool()
def search_academic(query: str, source: str = "semantic_scholar", num_results: int = 3) -> str:
      """Search academic sources for scholarly information.
      
      Args:
            query: Search query
            source: Academic source to use ("semantic_scholar", "arxiv", "pubmed")
            num_results: Number of results (1-10)
      """
      sources = {
            "semantic_scholar": {
                  "url": "https://api.semanticscholar.org/graph/v1/paper/search",
                  "params": {
                  "query": query,
                  "limit": min(max(1, num_results), 10),
                  "fields": "title,authors,venue,year,abstract,url"
                  },
                  "headers": {}
            },
            "arxiv": {
                  "url": f"http://export.arxiv.org/api/query?search_query=all:{query}&start=0&max_results={min(max(1, num_results), 10)}",
                  "params": {},
                  "headers": {}
            },
            "pubmed": {
                  "url": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
                  "params": {
                  "db": "pubmed",
                  "term": query,
                  "retmode": "json",
                  "retmax": min(max(1, num_results), 10)
                  },
                  "headers": {}
            }
      }
      
      if source not in sources:
            return f"Invalid source. Choose from: {', '.join(sources.keys())}"
      
      api_config = sources[source]
      
      try:
            if source == "arxiv":
                  # Special handling for arXiv's XML response
                  import xml.etree.ElementTree as ET
                  response = requests.get(api_config["url"])
                  root = ET.fromstring(response.content)
                  
                  ns = {'atom': 'http://www.w3.org/2005/Atom'}
                  entries = root.findall('./atom:entry', ns)
                  
                  formatted_results = []
                  for entry in entries:
                        title = entry.find('./atom:title', ns).text.strip()
                        authors = ", ".join([author.find('./atom:name', ns).text for author in entry.findall('./atom:author', ns)])
                        summary = entry.find('./atom:summary', ns).text.strip()
                        link = entry.find('./atom:id', ns).text
                        
                        formatted_results.append(
                              f"Title: {title}\n"
                              f"Authors: {authors}\n"
                              f"Link: {link}\n"
                              f"Summary: {summary[:300]}...\n"
                        )
                  
                  return "\n\n".join(formatted_results)
                  
            elif source == "semantic_scholar":
                  response = requests.get(api_config["url"], params=api_config["params"], headers=api_config["headers"])
                  results = response.json()
                  
                  if "data" not in results:
                        return f"No results found in Semantic Scholar for query: {query}"
                  
                  formatted_results = []
                  for paper in results["data"]:
                        authors = ", ".join([author.get("name", "Unknown") for author in paper.get("authors", [])])
                        formatted_results.append(
                              f"Title: {paper.get('title', 'No title')}\n"
                              f"Authors: {authors}\n"
                              f"Year: {paper.get('year', 'Unknown')}\n"
                              f"Venue: {paper.get('venue', 'Unknown')}\n"
                              f"URL: {paper.get('url', 'No URL available')}\n"
                              f"Abstract: {paper.get('abstract', 'No abstract available')[:300]}...\n"
                        )
                  
                  return "\n\n".join(formatted_results)
                  
            elif source == "pubmed":
                  response = requests.get(api_config["url"], params=api_config["params"], headers=api_config["headers"])
                  results = response.json()
                  
                  if "esearchresult" not in results or "idlist" not in results["esearchresult"]:
                        return f"No results found in PubMed for query: {query}"
                  
                  # Get details for each paper ID
                  id_list = results["esearchresult"]["idlist"]
                  if not id_list:
                        return f"No results found in PubMed for query: {query}"
                  
                  # Fetch details
                  summary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
                  summary_params = {
                  "db": "pubmed",
                  "id": ",".join(id_list),
                  "retmode": "json"
                  }
                  
                  summary_response = requests.get(summary_url, params=summary_params)
                  summary_results = summary_response.json()
                  
                  formatted_results = []
                  for paper_id in id_list:
                        paper = summary_results["result"][paper_id]
                        formatted_results.append(
                              f"Title: {paper.get('title', 'No title')}\n"
                              f"Authors: {', '.join(paper.get('authors', [{'name': 'Unknown'}])[0].get('name', 'Unknown'))}\n"
                              f"Journal: {paper.get('fulljournalname', 'Unknown')}\n"
                              f"Year: {paper.get('pubdate', 'Unknown').split()[0]}\n"
                              f"PubMed ID: {paper_id}\n"
                              f"Link: https://pubmed.ncbi.nlm.nih.gov/{paper_id}/\n"
                        )
                  
                  return "\n\n".join(formatted_results)
                  
      except Exception as e:
            return f"Error performing academic search via {source}: {str(e)}"

@mcp.tool()
def unified_search(query: str, sources: List[str] = ["google"], num_results: int = 2) -> str:
      """Search multiple sources at once and combine results.
      
      Args:
            query: Search query
            sources: List of sources to search (google, serper, semantic_scholar, arxiv, pubmed)
            num_results: Number of results per source
      """
      available_sources = {
            "google": search_google,
            "serper": search_serper,
            "semantic_scholar": lambda q, n=num_results: search_academic(q, "semantic_scholar", n),
            "arxiv": lambda q, n=num_results: search_academic(q, "arxiv", n),
            "pubmed": lambda q, n=num_results: search_academic(q, "pubmed", n)
      }
      
      # Validate sources
      valid_sources = [s for s in sources if s in available_sources]
      if not valid_sources:
            return f"No valid sources specified. Choose from: {', '.join(available_sources.keys())}"
      
      all_results = {}
      for source in valid_sources:
            search_func = available_sources[source]
            try:
                  results = search_func(query, num_results)
                  all_results[source] = results
            except Exception as e:
                  all_results[source] = f"Error searching {source}: {str(e)}"
      
      # Format combined results
      formatted_output = []
      for source, results in all_results.items():
            formatted_output.append(f"=== {source.upper()} RESULTS ===\n{results}\n")
      
      return "\n\n".join(formatted_output)

@mcp.tool()
def analyze_topic(topic: str, depth: str = "medium") -> str:
      """Analyze a research topic at different depths of detail.
      
      This tool performs a comprehensive analysis by searching multiple sources
      and synthesizing the information.
      
      Args:
            topic: The research topic to analyze
            depth: Level of analysis - "brief", "medium", or "comprehensive"
      """
      # Define search parameters based on depth
      depth_config = {
            "brief": {"num_results": 2, "sources": ["google"]},
            "medium": {"num_results": 3, "sources": ["google", "semantic_scholar"]},
            "comprehensive": {"num_results": 5, "sources": ["google", "semantic_scholar", "arxiv"]}
      }
      
      # Use default if depth not recognized
      config = depth_config.get(depth, depth_config["medium"])
      
      # Get information from multiple sources
      search_results = unified_search(
            query=topic, 
            sources=config["sources"],
            num_results=config["num_results"]
      )
      
      # Create analysis introduction based on depth
      depth_intro = {
            "brief": f"Brief overview of {topic}:",
            "medium": f"Medium-depth analysis of {topic}:",
            "comprehensive": f"Comprehensive examination of {topic}:"
      }
      # Ask Azure OpenAI to generate a real analysis
      try:
            response = llm.chat.completions.create(
                  deployment_id=AZURE_DEPLOYMENT_NAME,
                  messages=[
                        {"role": "system", "content": f"You are a research assistant. Provide a detailed {depth} analysis of a topic based on gathered content."},
                        {"role": "user", "content": f"Topic: {topic}\n\nSearch Results:\n{search_results}"}
                  ],
                  temperature=0.5,
                  max_tokens=1000
            )
            return response.choices[0].message.content
      except Exception as e:
            return f"Error generating analysis: {str(e)}"


@mcp.tool()
def fact_check(claim: str) -> dict:
      """Verify a factual claim using Azure OpenAI and web results."""
      
      # Step 1: Search the web for verification context
      verification_queries = [
            f"is it true that {claim}",
            f"fact check {claim}",
            f"evidence for {claim}"
      ]

      search_results = []
      for query in verification_queries:
            result = search_google(query, num_results=3)
            search_results.append(result)

      combined_text = "\n\n".join(search_results)

      # Step 2: Use Azure OpenAI to assess the claim
      prompt = (
            f"Analyze the following claim and determine if it is true, false, or inconclusive "
            f"based on the evidence provided. Give a short explanation and confidence level.\n\n"
            f"Claim: {claim}\n\n"
            f"Evidence:\n{combined_text[:3000]}"
      )

      try:
            response = llm.chat.completions.create(
                  deployment_id=AZURE_DEPLOYMENT_NAME,
                  messages=[
                  {"role": "system", "content": "You are a fact-checking expert."},
                  {"role": "user", "content": prompt}
                  ],
                  temperature=0.3,
                  max_tokens=600
            )
            content = response.choices[0].message.content
            return {
                  "claim": claim,
                  "assessment": content,
                  "search_context": combined_text[:1000] + ("..." if len(combined_text) > 1000 else "")
            }
      except Exception as e:
            return {
                  "claim": claim,
                  "assessment": "Error",
                  "error": str(e)
            }


@mcp.tool()
def summarize_text(text: str, length: str = "medium") -> str:
      """Summarize text using Azure OpenAI."""
      prompt = f"Summarize this text in a {length} way:\n\n{text}"

      try:
            response = llm.chat.completions.create(
                  deployment_id=AZURE_DEPLOYMENT_NAME,
                  messages=[{"role": "user", "content": prompt}],
                  temperature=0.5,
                  max_tokens=512
            )
            return response.choices[0].message.content
      except Exception as e:
            return f"Error summarizing with Azure OpenAI: {str(e)}"


if __name__ == "__main__":
      mcp.run(transport="stdio")