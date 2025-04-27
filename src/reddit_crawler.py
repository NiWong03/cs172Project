import os
import sys
import json
import praw
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

CLIENT_ID= ""
CLIENT_SECRET= ""
USER_AGENT= ""

reddit = praw.Reddit(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    user_agent=USER_AGENT
)