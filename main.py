import json
import os
import sys
import requests
import time
from openai import OpenAI


with open("keys.json") as f:
    keys = json.load(f)

open_ai_key = keys["OPEN_AI_KEY"]
n8n_key = keys["N8N_KEY"]


def get_response(messages):
    client = OpenAI(api_key=open_ai_key)
    completion = client.chat.completions.create(model='gpt-4o-mini', messages=messages)
    return completion.choices[0].message.content


# test_messages = [
#     {
#         "role": "system",
#         "content": "You are a helpful assistant."
#     },
#     {
#         "role": "user",
#         "content": "What is the capital of France?"
#     }
# ]


def create_workflow(name, nodes = [], connections = {}):
    url = "https://n8n.squarelight.ai/api/v1"

    workflow = {
        "name": name,
        "nodes": nodes,
        "connections": connections,
        "settings": {
            "saveExecutionProgress": True,
            "saveManualExecutions": True,
            "saveDataErrorExecution": "all",
            "saveDataSuccessExecution": "all",
            "executionTimeout": 3600,
            "errorWorkflow": "VzqKEW0ShTXA5vPj",
            "timezone": "America/New_York",
            "executionOrder": "v1"
        },
    }

    response = requests.post(f"{url}/workflows", headers={"X-N8N-API-KEY": n8n_key}, json=workflow)
    if response.status_code != 200:
        print(response.text)
        return None
    return response.json()

    

NODE_TYPES = {
    "n8n-nodes-base":[
        "n8n-nodes-base.manualTrigger"
    ],
    "@n8n/n8n-nodes-langchain":[
        "@n8n/n8n-nodes-langchain.agent",
        "@n8n/n8n-nodes-langchain.lmChatOpenAi"
    ]
}

def create_node(name, position, type, parameters = {}):
    """
    Create a node object

    Args:
    name (str): The name of the node
    position (list): The position of the node on the canvas
    type (str): The type of the node
    """

    return {
        "name": name,
        "type": type,
        "position": position
    }


test_nodes = [
    create_node("Start", [0,0], "n8n-nodes-base.manualTrigger"),
    create_node("OpenAI", [200,0], "@n8n/n8n-nodes-langchain.agent"),
]


test_connections = {
    "Start": {
      "main": [
        [
          {
            "node": "OpenAI",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  }


# get date and time as str
def get_date_time():
    return time.strftime("%Y-%m-%d %H:%M:%S")

work_flow = create_workflow("Test @ "+ get_date_time(), test_nodes, test_connections)
