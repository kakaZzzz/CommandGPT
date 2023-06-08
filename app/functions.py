import os
from dotenv import load_dotenv
import re
import json
from agents.json import JsonAgent

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
    

def redPrint(*s):
    return print("\033[91m"+ " ".join(s) +"\033[0m")

def greenPrint(*s):
    return print("\033[92m"+ " ".join(s) +"\033[0m")

def yellowPrint(*s):
    return print("\033[93m"+ " ".join(s) +"\033[0m")

def bluePrint(*s):
    return print("\033[94m"+ " ".join(s) +"\033[0m")

def purplePrint(*s):
    return print("\033[95m"+ " ".join(s) +"\033[0m")

def cyanPrint(*s):
    return print("\033[96m"+ " ".join(s) +"\033[0m")

def jsonStr(s):
    matchObj = re.search( r'(\{.*\})', s, re.M|re.I|re.S)
    if matchObj:
        return matchObj[0]
    else:
        return ""

def json2value(s):
    s=jsonStr(s)
    print(s)
    try:
        v = json.loads(s)
        return v
    except Exception as r:
        print("[-]Json解析出错: ", r)

        res = JsonAgent().run({
            "json": s,
            "error": r
        })

        print(res)
        return json2value(res)

def json2File(s, file):
    with open(file, 'w') as f:
        json.dump(s, f, indent=4, ensure_ascii=False)

def jsonFromFile(file):
    with open(file, 'r') as f:
        return json.loads(f.read())
    
def githubFix(s):
    """github 替换为 kgithub"""
    new = s.replace('github', 'kgithub')
    return new