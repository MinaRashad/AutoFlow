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

# get date and time as str
def get_date_time():
    return time.strftime("%Y-%m-%d %H:%M:%S")

work_flow = create_workflow("Test @ "+ get_date_time(), test_nodes, test_connections)
