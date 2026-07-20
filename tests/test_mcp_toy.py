import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "notebooks"))

from lab_core.mcp_toy import (  # noqa: E402
    METHOD_NOT_FOUND,
    PROTOCOL_VERSION,
    ToyMCPClient,
    ToyMCPServer,
)
from lab_core.patterns import run_tool_loop  # noqa: E402


def build_server() -> ToyMCPServer:
    server = ToyMCPServer("test-server")
    server.add_tool(
        "echo",
        "Echo the message back.",
        {"type": "object", "properties": {"message": {"type": "string"}}, "required": ["message"]},
        lambda args: args["message"],
    )
    server.add_resource("lab://notes", "Notes", "line one")
    server.add_prompt("greet", "Greeting template", "Hello, {name}!")
    return server


class ToyMCPTests(unittest.TestCase):
    def test_handshake_negotiates_version_and_capabilities(self):
        client = ToyMCPClient(build_server())
        result = client.connect()
        self.assertEqual(result["protocolVersion"], PROTOCOL_VERSION)
        self.assertIn("tools", result["capabilities"])
        # initialize request plus initialized notification, both recorded
        self.assertEqual(len(client.transcript), 2)
        self.assertIsNone(client.transcript[1]["response"])

    def test_tools_are_discoverable_and_callable(self):
        client = ToyMCPClient(build_server())
        client.connect()
        tools = client.list_tools()
        self.assertEqual([t["name"] for t in tools], ["echo"])
        self.assertIn("inputSchema", tools[0])
        result = client.call_tool("echo", {"message": "hi"})
        self.assertFalse(result["isError"])
        self.assertEqual(result["content"][0]["text"], "hi")

    def test_tool_failure_is_a_result_not_a_protocol_error(self):
        client = ToyMCPClient(build_server())
        client.connect()
        result = client.call_tool("echo", {})  # missing required argument
        self.assertTrue(result["isError"])
        self.assertIn("message", result["content"][0]["text"])

    def test_unknown_method_returns_json_rpc_error(self):
        server = build_server()
        response = server.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/subscribe"})
        self.assertEqual(response["error"]["code"], METHOD_NOT_FOUND)
        client = ToyMCPClient(server)
        with self.assertRaises(RuntimeError):
            client.request("tools/subscribe")

    def test_resources_and_prompts(self):
        client = ToyMCPClient(build_server())
        client.connect()
        contents = client.read_resource("lab://notes")["contents"]
        self.assertEqual(contents[0]["text"], "line one")
        prompt = client.get_prompt("greet", {"name": "Ada"})
        self.assertEqual(prompt["messages"][0]["content"]["text"], "Hello, Ada!")

    def test_mcp_client_can_serve_as_tool_loop_boundary(self):
        client = ToyMCPClient(build_server())
        client.connect()
        tools = {
            t["name"]: (lambda args, name=t["name"]: client.call_tool(name, args)["content"][0]["text"])
            for t in client.list_tools()
        }

        def policy(goal, trace):
            if not trace:
                return {"tool": "echo", "input": {"message": "evidence"}}
            return {"final": trace[-1]["observation"]}

        result = run_tool_loop("relay", policy, tools, max_steps=2)
        self.assertTrue(result.completed)
        self.assertEqual(result.answer, "evidence")


if __name__ == "__main__":
    unittest.main()
