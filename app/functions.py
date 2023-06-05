import os
from dotenv import load_dotenv
import re

def load_env():
    # Load environment variables from .env file
    load_dotenv(verbose=True)

    # Get environment variables
    env_vars = os.environ

    # Return environment variables as dictionary
    return dict(env_vars)

def getGithubRepo(url):
    matchObj = re.search( r'com/(.*)$', url, re.M|re.I)
    if matchObj:
        return "https://raw.githubusercontent.com/"+matchObj[1]+"/main/README.md"