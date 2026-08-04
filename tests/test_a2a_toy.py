import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "notebooks"))

from lab_core.a2a_toy import (  # noqa: E402
    CANCELED,
    COMPLETED,
    INPUT_REQUIRED,
    METHOD_NOT_FOUND,
    TASK_NOT_CANCELABLE,
    WELL_KNOWN_PATH,
    ToyA2AClient,
    ToyA2ANetwork,
    ToyA2AServer,
    ToyAgentCard,
)


def build_network() -> ToyA2ANetwork:
    def echo(text):
        return {"artifact": f"echo: {text}"}

    def clarifier(text):
        if "oslo" in text.lower():
            return {"artifact": "Itinerary for Oslo"}
        return {"input_required": "Which city?"}

    network = ToyA2ANetwork()
    card = ToyAgentCard("echo-agent", "Echoes input.", "https://echo.lab", skills=[{"id": "echo"}])
    network.register(ToyA2AServer(card, echo))
    trip_card = ToyAgentCard("trip-agent", "Plans trips.", "https://trips.lab")
    network.register(ToyA2AServer(trip_card, clarifier))
    return network


class ToyA2ATests(unittest.TestCase):
    def test_discovery_returns_card_at_well_known_path(self):
        client = ToyA2AClient(build_network())
        card = client.discover("https://echo.lab")
        self.assertEqual(card["name"], "echo-agent")
        self.assertEqual(card["supportedInterfaces"][0]["protocolBinding"], "JSONRPC")
        self.assertTrue(client.transcript[0]["get"].endswith(WELL_KNOWN_PATH))

    def test_send_message_completes_task_with_artifact(self):
        client = ToyA2AClient(build_network())
        task = client.send_message("https://echo.lab", "hello")
        self.assertEqual(task["status"]["state"], COMPLETED)
        self.assertEqual(task["artifacts"][0]["parts"][0]["text"], "echo: hello")
        self.assertEqual(client.get_task("https://echo.lab", task["id"])["id"], task["id"])

    def test_input_required_pauses_then_follow_up_completes(self):
        client = ToyA2AClient(build_network())
        task = client.send_message("https://trips.lab", "plan a trip")
        self.assertEqual(task["status"]["state"], INPUT_REQUIRED)
        self.assertEqual(task["status"]["update"]["parts"][0]["text"], "Which city?")
        done = client.send_message("https://trips.lab", "Oslo", task_id=task["id"])
        self.assertEqual(done["status"]["state"], COMPLETED)
        self.assertEqual(done["artifacts"][0]["parts"][0]["text"], "Itinerary for Oslo")

    def test_cancel_paused_task_and_refuse_terminal_cancel(self):
        client = ToyA2AClient(build_network())
        paused = client.send_message("https://trips.lab", "plan a trip")
        self.assertEqual(client.cancel_task("https://trips.lab", paused["id"])["status"]["state"], CANCELED)
        done = client.send_message("https://echo.lab", "hi")
        with self.assertRaises(RuntimeError) as ctx:
            client.cancel_task("https://echo.lab", done["id"])
        self.assertIn(str(TASK_NOT_CANCELABLE), str(ctx.exception))

    def test_unknown_method_returns_json_rpc_error(self):
        client = ToyA2AClient(build_network())
        with self.assertRaises(RuntimeError) as ctx:
            client.request("https://echo.lab", "SubscribeToTask", {})
        self.assertIn(str(METHOD_NOT_FOUND), str(ctx.exception))

    def test_transcript_records_every_exchange(self):
        client = ToyA2AClient(build_network())
        client.discover("https://echo.lab")
        client.send_message("https://echo.lab", "one")
        self.assertEqual(len(client.transcript), 2)
        self.assertEqual(client.transcript[1]["request"]["method"], "SendMessage")
        self.assertIn("result", client.transcript[1]["response"])


if __name__ == "__main__":
    unittest.main()
