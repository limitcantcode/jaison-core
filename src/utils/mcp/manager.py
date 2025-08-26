import os
import json
import datetime
import re
import urllib
import logging
from typing import List, Dict
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
from mcp.types import (
    TextContent,
    ImageContent,
    EmbeddedResource,
    TextResourceContents,
    BlobResourceContents
)

from utils.config import Config
from utils.operations import OperationManager, OpRoles

def parse_tool_result(result):
    if isinstance(result, TextContent):
        return result.text
    elif isinstance(result, ImageContent):
        return result.data
    elif isinstance(result, EmbeddedResource):
        return result.resource
    elif isinstance(result, TextResourceContents):
        return result.text
    elif isinstance(result, BlobResourceContents):
        return result.blob
    else:
        raise Exception("Unknown result type")

def details_to_response_prompt(details):
    tools = details['tools']
    resources = details['resources']
    templates = details['templates']
    
    prompt = ""
    
    for tool in tools:
        name = tool.name
        description = tool.description
        prompt += f"<{name}> {description}\n\n"
        
    for resource in resources:
        name = resource.name
        description = resource.description
        prompt += f"<{name}> {description}\n"
        
    for template in templates:
        name = template.name
        description = template.description
        prompt += f"<{name}> {description}\n\n"
        
    return prompt
    
def details_to_tool_prompt(details):
    tools = details['tools']
    resources = details['resources']
    templates = details['templates']
    
    prompt = ""
    
    for tool in tools:
        name = tool.name
        description = tool.description
        inputSchema = json.dumps(tool.inputSchema)
        prompt += f"<{name}> {description}\nThis is the input schema for {name}: {inputSchema}\n"
        
    for resource in resources:
        name = resource.name
        description = resource.description
        prompt += f"<{name}> {description}\n"
        
    for template in templates:
        name = template.name
        description = template.description
        uri_template = template.uriTemplate
        prompt += f"<{name}> {description}\nThis is the URI template: {uri_template}\n"
        
    return prompt

class MCPClient:
    '''Managing of a single server instance'''
    
    def __init__(self, mcp_id: str, params: StdioServerParameters):
        self.mcp_id = mcp_id
        self.params = params
        self.server_generator = None
        self.server_read = None
        self.server_write = None
        self.session = None
        
        self.tools = list()
        self.resources = list()
        self.templates = list()
        
        self.tool_names = list()
        self.resource_names = list()
        self.template_names = list()
        
        self.tool_prompt = ""
        self.response_prompt = ""
        
    async def start(self):
        self.server_generator = stdio_client(self.params)
        logging.debug("starting context")
        self.server_read, self.server_write = await self.server_generator.__aenter__()
        logging.debug("{} {}".format(type(self.server_read), type(self.server_write)))
        logging.debug("starting session")
        self.session = ClientSession(
            self.server_read,
            self.server_write,
            read_timeout_seconds=datetime.timedelta(seconds=10),
            sampling_callback=self.handle_sampling_message
        )
        
        logging.debug("initializing session")
        await self.session.__aenter__()
        await self.session.initialize()
        
        details = await self.get_details()
        self.tool_prompt = details_to_tool_prompt(details)
        self.response_prompt = details_to_response_prompt(details)
        
    async def close(self):
        await self.session.__aexit__(None, None, None)
        await self.server_generator.__aexit__(None, None, None)
        
    async def get_details(self):
        try:
            self.tools = (await self.session.list_tools()).tools
        except:
            pass
        try:
            self.resources = (await self.session.list_resources()).resources
        except:
            pass
        try:
            self.templates = (await self.session.list_resource_templates()).resourceTemplates
        except:
            pass
        
        for tool in self.tools:
            self.tool_names.append(tool.name)
        for resource in self.resources:
            self.resource_names.append(resource.name)
        for template in self.templates:
            self.template_names.append(template.name)
        
        return {
            "tools": self.tools,
            "resources": self.resources,
            "templates": self.templates
        }
    
    async def handle_sampling_message(
        self,
        ctx,
        message: types.CreateMessageRequestParams
    ) -> types.CreateMessageResult:
        try:
            metadata = message.metadata or dict()
            sample_type = metadata.get("sample_type", "t2t")
            if sample_type == "t2t":
                response_stream = OperationManager().use_operation(
                    OpRoles.MCP,
                    {
                        "system_prompt": message.systemPrompt,
                        "user_prompt": message.messages[0].content.text 
                    }
                )

                response = ""
                async for chunk_out in response_stream:
                    response += chunk_out["content"]

                return types.CreateMessageResult(
                    role="assistant",
                    content=types.TextContent(
                        type="text",
                        text=response,
                    ),
                    model="mcp",
                    stopReason="endTurn",
                )
            elif sample_type == "embedding":
                response_stream = OperationManager().use_operation(
                    OpRoles.EMBEDDING,
                    {
                        "content": message.systemPrompt[:10000],
                    }
                )

                response = ""
                async for chunk_out in response_stream:
                    response += chunk_out["embedding"]

                return types.CreateMessageResult(
                    role="assistant",
                    content=types.TextContent(
                        type="text",
                        text=response,
                    ),
                    model="embedding",
                    stopReason="endTurn",
                )
        except Exception as err:
            logging.error("MCP sampler encountered an issue", exc_info=True)
            return ""
        
class MCPManager:
    tooling_prompt = """
You are calling tools based on the user input to gather more information to enrich a role-playing response and to perform relevant actions. Only reply with the appropriate tool calls and nothing else.
The tool name is in between angle brackets "<>". For example, a line with <tool-name> indicates a tool with name "tool-name". On this line, you will also see a description of what this tool does, and it may have a line after that containing a input schema or uri template with information of what parameters the tool takes.
Input schemas are JSON objects, and the parameters for the function are the keys of object "properties" and their type is described in their paired object under key "type". For example, with input schema {"type": "object", "properties": {"name": {"type": "number"}, "description": {"type": "string"}}}, you have 2 parameters, name of type number and description of type string.
URI templates have the parameters in curly brackets "{}". For example internet://{name}&{description} has parameters "name" and "description". They are any type.
To call a tool, separate each tool call on a new line. Each line will have the following format: <name> {"param1":value1 "param2":value2}. It starts with the tool name followed by a JSON where each key is a parameter and the value is the associated value. If the value is a string, surround the string with "". Do not include " in values otherwise otherwise, even inside the string. If there are no parameters, just include the name and an empty JSON object. For example: <name> {}
For example, to call tool <internet> with URI template internet://{name}&{description} with the name Limit and description "Limit is an idiot", you would respond with: <internet> name="Limit" description="Limit is an idiot"
If you don't want to call any tools, simply reply with "<no-tool>"
Below is a list of descriptions for all available tool:\n
"""

#     response_prompt = """
# You are an assistant answer a user's question.
# You will be given the user's question under the header <QUESTION>. Answer this using the additional information. Do not hallucinate.
# You are given additional information to the actions and context retrieved prior to answering under the header <CONTEXT>.
# This additional information will each be on a new line, formated as follows: context_name: context_result
# For example, context by the name of "memories" that gave context "you are an ai" will look like "memories: you are an ai"
# Below is a list of all available contexts and their descriptions:
# """

    pattern = re.compile(r"^<[\S]*>")
            
    def __init__(self):
        # servers are loaded at start and at no other point
        # self.client_params: List[StdioServerParameters] = list()
        self.clients: Dict[str, MCPClient] = dict()
        
    async def start(self):
        config = Config()
        for mcp_detail in config.mcp:
            await self.load_mcp(mcp_detail)
        
    async def load_mcp(self, mcp_detail: Dict):
        # TODO validate the mcp_detail 
        
        params = StdioServerParameters(
            command=mcp_detail['command'],  # Executable
            args=mcp_detail['args'],  # Optional command line arguments
            env=os.environ,  # Optional environment variables
            cwd=mcp_detail['cwd']
        )
        client = MCPClient(mcp_detail["id"], params)
        await client.start()
        self.clients[mcp_detail['id']] = client
        
    async def close_mcp(self, mcp_id: str):
        target = self.clients.get(mcp_id, None)
        if target:
            await target.close()
            del self.clients[mcp_id]
            
    def get_tooling_prompt(self):
        prompt = self.tooling_prompt
        for client_key in self.clients:
            prompt += self.clients[client_key].tool_prompt
            
        return prompt
    
    def get_response_prompt(self):
        # prompt = self.response_prompt
        prompt = ""
        for client_key in self.clients:
            prompt += self.clients[client_key].response_prompt
            
        return prompt
            
    async def use(self, tooling_response: str):
        tool_calls = tooling_response.split("\n")
        
        result_list = list()
        
        for tool_call in tool_calls:
            result = None
            tool_name = ""
            try:
                match = self.pattern.search(tool_call)
                if match is None: continue
                name_token = tool_call[:match.span()[1]]
                tool_name = name_token.lstrip("<").rstrip(">")
                if name_token == "no_op": continue
                tool_call = tool_call[match.span()[1]:].rstrip(" ")
                input_json = json.loads(tool_call) if len(tool_call) else dict()
                
                tool = {
                    "name": name_token,
                    "input": input_json
                }
                
                for client in self.clients:
                    if tool_name in self.clients[client].tool_names:
                        result = await self.clients[client].session.call_tool(tool_name, arguments=tool['input'])
                        result = parse_tool_result(result.content[0])
                        break
                    elif tool_name in self.clients[client].resource_names:
                        uri = None
                        for resource in self.clients[client].resources:
                            if resource.name == tool_name:
                                uri = resource.uri
                                break
                        result = await self.clients[client].session.read_resource(uri)
                        result = parse_tool_result(result.contents[0])
                        break
                    elif tool_name in self.clients[client].template_names:
                        uri_template = None
                        for templates in self.clients[client].templates:
                            if templates.name == tool_name:
                                uri_template = templates.uriTemplate
                                break
                        for key in tool['input']:
                            if isinstance(tool['input'][key], str):
                                urllib.parse.quote(tool['input'][key])
                                tool['input'][key] = urllib.parse.quote(tool['input'][key])
                        logging.debug("Calling resource: {} {} {}".format(tool_name, tool['input'], uri_template))
                        logging.debug(uri_template.format(**tool['input']))
                        result = await self.clients[client].session.read_resource(
                            uri_template.format(**tool['input'])
                        )
                        result = parse_tool_result(result.contents[0])
                        break
            except Exception as err:
                logging.critical("Error occured during MCP", exc_info=True)
                result = "Attempt to use MCP tool failed due to {}".format(str(err))
            if result:
                result_list.append((tool_name, result))
        
        return result_list

    async def close(self):
        for client_key in self.clients:
            await self.clients[client_key].close()