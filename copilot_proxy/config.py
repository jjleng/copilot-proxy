import os

MODEL_URL = os.getenv("MODEL_URL")
MODEL_API_KEY = os.getenv("MODEL_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME")

# The patterns of the urls that we want to pay attention to
URLS_OF_INTEREST = r"api\.github|copilot-codex"
