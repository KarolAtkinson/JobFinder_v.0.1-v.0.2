import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from cv_optimiser.local_ai import MODEL_ID, OllamaClient


class OllamaTestHandler(BaseHTTPRequestHandler):
    requests: list[tuple[str, dict[str, object]]] = []
    models: list[dict[str, str]] = []
    chat_content = '{"rewrites":[]}'

    def do_GET(self) -> None:
        body = json.dumps({"models": self.models}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        self.requests.append((self.path, payload))
        if self.path == "/api/pull":
            body = (
                b'{"status":"downloading","total":100,"completed":50}\n'
                b'{"status":"success"}\n'
            )
            self.send_response(200)
            self.send_header("Content-Type", "application/x-ndjson")
        else:
            body = json.dumps({"message": {"content": self.chat_content}}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


class OllamaHttpClientTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), OllamaTestHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def setUp(self) -> None:
        OllamaTestHandler.requests.clear()
        OllamaTestHandler.models = [{"name": MODEL_ID}]
        OllamaTestHandler.chat_content = '{"rewrites":[]}'

    def test_checks_local_model_inventory(self) -> None:
        self.assertTrue(OllamaClient(self.base_url).is_model_installed())
        OllamaTestHandler.models = [{"name": "some-other-model"}]
        self.assertFalse(OllamaClient(self.base_url).is_model_installed())

    def test_sends_rewrite_request_to_local_chat_api(self) -> None:
        client = OllamaClient(self.base_url)

        response = client.chat("system", "user")

        self.assertEqual(response, '{"rewrites":[]}')
        path, payload = OllamaTestHandler.requests[-1]
        self.assertEqual(path, "/api/chat")
        self.assertEqual(payload["model"], MODEL_ID)
        self.assertEqual(payload["stream"], False)
        self.assertEqual(payload["messages"], [
            {"role": "system", "content": "system"},
            {"role": "user", "content": "user"},
        ])

    def test_streams_reply_and_reports_progress(self) -> None:
        client = OllamaClient(self.base_url)
        counts: list[int] = []
        client.on_progress = counts.append

        response = client.chat("system", "user")

        self.assertEqual(response, '{"rewrites":[]}')
        self.assertEqual(counts, [1])
        self.assertEqual(OllamaTestHandler.requests[-1][1]["stream"], True)

    def test_reports_model_download_progress(self) -> None:
        progress: list[tuple[str, int | None]] = []

        OllamaClient(self.base_url).pull_model(lambda status, percent: progress.append((status, percent)))

        self.assertEqual(progress, [("downloading", 50), ("success", None)])
        self.assertEqual(OllamaTestHandler.requests[-1][0], "/api/pull")
