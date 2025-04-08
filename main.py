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

    # Typical Instances of 15 Most used Nodes from scraped n8n AI templates
    # 1. n8n-nodes-base.stickyNote
    create_node("Sticky Note", [720, 1840], "n8n-nodes-base.stickyNote", {
        "color": 3,
        "width": 280,
        "height": 380,
        "content": "## LLM"
    }),

    # 2. n8n-nodes-base.set
    create_node("Chat Response", [1440, 1600], "n8n-nodes-base.set", {
        "options": {},
        "assignments": {
            "assignments": [
                {"id": "d6f68b1c-a6a6-44d4-8686-dc4dcdde4767", "name": "output", "type": "string", "value": "={{ $json.output }}"}
            ]
        }
    }),

    # 3. @n8n/n8n-nodes-langchain.agent
    create_node("AI Tools Agent", [1060, 1600], "@n8n/n8n-nodes-langchain.agent", {
        "text": "={{ $('When chat message received').item.json.chatInput }}",
        "options": {"systemMessage": "=## ROLE\nYou are a friendly, attentive, and helpful AI assistant..."},
        "promptType": "define"
    }),

    # 4. n8n-nodes-base.httpRequest
    create_node("Perform SerpAPI Search Request", [-780, 180], "n8n-nodes-base.httpRequest", {
        "url": "https://serpapi.com/search",
        "options": {},
        "sendQuery": True,
        "queryParameters": {
            "parameters": [
                {"name": "q", "value": "={{ $('Parse and Chunk JSON Data').item.json.chunk }}"},
                {"name": "api_key", "value": "={{ $credentials.SerpAPI.key }}"},
                {"name": "engine", "value": "google"}
            ]
        }
        # "credentials": {"SerpAPI": {"id": "some-id", "name": "SerpAPI account"}}  # Add if extending function
    }),

    # 5. n8n-nodes-base.telegram
    create_node("Telegram Response", [1440, 1260], "n8n-nodes-base.telegram", {
        "text": "={{ $json.output }}",
        "chatId": "=1234567891",
        "additionalFields": {"parse_mode": "HTML", "appendAttribution": False}
        # "credentials": {"telegramApi": {"id": "pAIFhguJlkO3c7aQ", "name": "Telegram account"}}  # Add if extending
    }),

    # 6. @n8n/n8n-nodes-langchain.lmChatOpenAi
    create_node("gpt-4o-mini", [820, 1900], "@n8n/n8n-nodes-langchain.lmChatOpenAi", {
        "options": {}
        # "credentials": {"openAiApi": {"id": "jEMSvKmtYfzAkhe6", "name": "OpenAi account"}}  # Add if extending
    }),

    # 7. @n8n/n8n-nodes-langchain.memoryBufferWindow
    create_node("Window Buffer Memory", [1140, 2000], "@n8n/n8n-nodes-langchain.memoryBufferWindow", {
        "sessionKey": "={{ $('When chat message received').item.json.sessionId }}",
        "sessionIdType": "customKey",
        "contextWindowLength": 50
    }),

    # 8. n8n-nodes-base.code
    create_node("Parse and Chunk JSON Data", [-1420, 160], "n8n-nodes-base.code", {
        "jsCode": "const rawText = $json.text; const cleanedText = rawText.replace(/```json|```/g, '').trim(); ..."
    }),

    # 9. n8n-nodes-base.merge
    create_node("Merge", [340, 1600], "n8n-nodes-base.merge", {}),

    # 10. n8n-nodes-base.splitInBatches
    create_node("Split Data for SerpAPI Batching", [-1100, 160], "n8n-nodes-base.splitInBatches", {
        "options": {}
    }),

    # 11. n8n-nodes-base.filter
    create_node("Exclude uncalled workflows", [1400, 0], "n8n-nodes-base.filter", {
        "options": {},
        "conditions": {
            "options": {"version": 2, "caseSensitive": True, "typeValidation": "strict"},
            "combinator": "and",
            "conditions": [
                {"id": "a1ccd5c3-ee85-412b-ac36-b68f9d2bc904", "operator": {"type": "number", "operation": "gt"}, "leftValue": "={{ $json.callers.length }}", "rightValue": 0}
            ]
        }
    }),

    # 12. n8n-nodes-base.webhook
    create_node("Listen for Telegram Events", [-480, 160], "n8n-nodes-base.webhook", {
        "path": "wbot",
        "options": {"binaryPropertyName": "data"},
        "httpMethod": "POST"
        # "webhookId": "097f36f3-1574-44f9-815f-58387e3b20bf"  # Generated by n8n, not set here
    }),

    # 13. n8n-nodes-base.googleDocs
    create_node("Retrieve Long Term Memories", [20, 1420], "n8n-nodes-base.googleDocs", {
        "operation": "get",
        "documentURL": "[Google Doc ID]"
        # "credentials": {"googleDocsOAuth2Api": {"id": "YWEHuG28zOt532MQ", "name": "Google Docs account"}}
    }),

    # 14. n8n-nodes-base.if
    create_node("Check User & Chat ID", [-80, 160], "n8n-nodes-base.if", {
        "options": {},
        "conditions": {
            "options": {"version": 2, "caseSensitive": True, "typeValidation": "strict"},
            "combinator": "and",
            "conditions": [
                {"id": "5fe3c0d8-bd61-4943-b152-9e6315134520", "operator": {"type": "string", "operation": "equals"}, "leftValue": "={{ $('Listen for Telegram Events').item.json.body.message.from.first_name }}", "rightValue": "={{ $json.first_name }}"}
            ]
        }
    }),

    # 15. @n8n/n8n-nodes-langchain.chatTrigger
    create_node("When chat message received", [-320, 1600], "@n8n/n8n-nodes-langchain.chatTrigger", {
        "options": {}
        # "webhookId": "8ba8fa53-2c24-47a8-b4dd-67b88c106e3d"  # Generated by n8n
    })
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

test_connections1 = {
    "Sticky Note": {
        "main": [[]]  # No connections typically
    },
    "Chat Response": {
        "main": [[{"node": "Telegram Response", "type": "main", "index": 0}]]
    },
    "AI Tools Agent": {
        "main": [[{"node": "Chat Response", "type": "main", "index": 0}]]
    },
    }
]

#task = sys.argv[1]
    
#generate_workflow(task)
st.title("Autoflow: AI Workflow Generator")

task = st.text_area("Task", "Create a workflow that sends an email when a new tweet is posted")

if st.button("Generate Workflow"):
    generate_workflow(task)
    

