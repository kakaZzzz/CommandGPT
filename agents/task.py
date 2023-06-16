# !/usr/bin/env python3
from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain


from langchain.prompts import (
    ChatPromptTemplate,
    PromptTemplate,
    SystemMessagePromptTemplate,
    AIMessagePromptTemplate,
    HumanMessagePromptTemplate,
)

import prompts.task_message as prompts
from tools import Tools

class  TaskAgent:
    def __init__(self) -> None:
        """

        """
        llm = ChatOpenAI(
            temperature = 0.9
        )
        system_message_prompt = SystemMessagePromptTemplate.from_template(prompts.system())
        human_message_prompt = HumanMessagePromptTemplate.from_template(prompts.human())
        chat_prompt = ChatPromptTemplate.from_messages([
            system_message_prompt,
            human_message_prompt
        ])

        self.tools = Tools()
        self.uesd_tools = ["shell", "change_dir"]
        self.chain = LLMChain(llm=llm, prompt=chat_prompt, verbose=True)

    def run(self, input):
        """

        @param input:
        @return:
        """
        input["tools"] = self.tools.inline_text(self.uesd_tools)

        return self.chain.run(input)