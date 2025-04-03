import json
import os
import sys
import requests
import time
from openai import OpenAI
import streamlit as st


with open("keys.json") as f:
    keys = json.load(f)

open_ai_key = keys["OPEN_AI_KEY"]
n8n_key = keys["N8N_KEY"]

with open("./n8n_nodes_docs.txt") as f:
    n8n_nodes_docs = f.read()


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
def create_workflow(name, nodes = [], connections ={})
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
```
work_flow = create_workflow("Test with adding a node", test_nodes, test_connections)

for any node, you can access its input from previous node by writing {{ $json }} (e.g. getting an input from LLM and want to send it as email)

Here is a documentation of some nodes and how to use them:

"""

system_prompt += n8n_nodes_docs

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

    only functions allowed are `create_node` and `create_workflow`. 
    Defining variables is allowed. If it does anything else, reply with "unsafe".
    Otherwise, reply with "safe"

    <code>
"""

def generate_workflow(task):
    messages = [
        {
            "role": "system",
            "content": system_prompt+planning_system.replace("<task>", task)
        }
        ]
    
    st.write("planning...")
    plan = get_response(messages)

    messages = [
        {
            "role": "system",
            "content": system_prompt+excuting_system.replace("<plan>", plan)
        }
        ]
    st.write("Generating workflow...")
    code = get_response(messages)

    messages = [
        {
            "role": "system",
            "content": system_prompt+safety_system+code
        }
        ]
    
    st.write("Checking safety...")
    safety = get_response(messages)

    if safety.lower() == "safe":
        st.write("Creating workflow...")
        code = code.replace("```python", "")
        code = code.replace("```", "")
        exec(code)
        st.write("Done")
        st.write("Check your n8n dashboard for the new workflow")
        st.write("https://n8n.squarelight.ai/")
    else:
        st.write("Warning: Unsafe code generated, check before excuting")
        st.write(code)
        # ask user with streamlit if they want to excute

        if st.button("Execute"):
            code = code.replace("```python", "")
            code = code.replace("```", "")
            exec(code)
            st.write("Done")
            st.write("Check your n8n dashboard for the new workflow")
            st.write("https://n8n.squarelight.ai/")
        else:
            st.write("Code not executed")


#task = sys.argv[1]
    
#generate_workflow(task)
st.title("Autoflow: AI Workflow Generator")

task = st.text_area("Task", "Create a workflow that sends an email when a new tweet is posted")

if st.button("Generate Workflow"):
    generate_workflow(task)
    

