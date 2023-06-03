# Desc: Main entry point for the application
# Auth: kaka
# Date: 2023-6-4
#

# intialize the environment variables
import app.functions as f
import os

envs = f.load_env()
os.environ["OPENAI_API_KEY"] = envs["OPENAI_API_KEY"]

from agents.goal import GoalAgent

print(GoalAgent().run({
    "goal": "请帮我安装python的dotenv库",
}))