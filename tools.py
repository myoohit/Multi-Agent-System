from langchain.tools import tool
import requests 
from bs4 import BeautifulSoup #web scraping 
from tavily import TavilyClient
import os
from dotenv import load_dotenv
load_dotenv()


tavily=TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))