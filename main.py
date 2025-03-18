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
        "position": position,
        "parameters": parameters
    }


system_prompt = """ You are a model created to generate workflow on n8n using their API.
This is the following functions and code you have access to

```python
def create_workflow(name, nodes = [], connections = {})
```

This function will create a new workflow with the given name, nodes and connections

```python
create_node(name, position, type, parameters = {})
```

This function will return a new node with the given name, position (list), type (string) and parameters (dict)

Here is an incomplete list of valid node types:
```python
NODE_TYPES = {
    "n8n-nodes-base":[
        "n8n-nodes-base.manualTrigger"
    ],
    "@n8n/n8n-nodes-langchain":[
        "@n8n/n8n-nodes-langchain.agent",
        "@n8n/n8n-nodes-langchain.lmChatOpenAi"
    ]
}
```

This is just an example of what node types look like and not meant to be exhaustive.

The connections object is an ordered map.

Here is a simple example of a manual trigger node connected to an OpenAI node

```python
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

work_flow = create_workflow("Test with adding a node", test_nodes, test_connections)
```
"""

planning_system = """
Main task now:
Create a detailed plan for how you would make a workflow that does the following:
<task>
Important things to consider:
- triggers: what will start the workflow?
- nodes: what nodes will you need?
- connections: how will the nodes be connected?"""

excuting_system = """" The following plan was formulated:
<plan>
Using this plan, return the respective code that would create the workflow. Respond with code only"""

safety_system = """" 
    The following python code was generated to create a workflow.
    If the code is doing anythin other than creating a workflow, respond with "unsafe". otherwise, 
    response with "safe". Respond with only one word.

    only functions allowed are create_node and create_workflow. If these are the only functions used, it is safe.

    <code>
"""
# get date and time as str
def get_date_time():
    return time.strftime("%Y-%m-%d %H:%M:%S")

def generate_workflow(task):
    print("TASK: ", task)
    messages = [
        {
            "role": "system",
            "content": system_prompt+planning_system.replace("<task>", task)
        }
        ]
    
    print("planning...")
    plan = get_response(messages)

    messages = [
        {
            "role": "system",
            "content": system_prompt+excuting_system.replace("<plan>", plan)
        }
        ]
    print("Generating workflow...")
    code = get_response(messages)

    messages = [
        {
            "role": "system",
            "content": system_prompt+safety_system+code
        }
        ]
    
    print("Checking safety...")
    safety = get_response(messages)

    if True or safety.lower() == "safe":
        print("Creating workflow...")
        code = code.replace("```python", "")
        code = code.replace("```", "")
        exec(code)
    else:
        print("Unsafe code generated")
        print(code)
    print("Done")

task = """
Create a workflow named "Email automation"
That sends an email every week to mina@uni.minerva.edu with the word hello
"""
    
generate_workflow(task)