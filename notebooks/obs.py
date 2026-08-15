"""Optional observability helpers for the agentic-lab notebooks (taught in notebook 27).

Ported from the dspy-lab course's ``obs.py`` and adapted to this lab: DSPy has
autolog integrations, so there the helpers only had to switch tracing on; here
the lab's own span layer (``lab_core.trace``) does the tracing, and these
helpers provide the *sinks* that bridge it into the UIs, plus the same
find-or-start server management.

Usage, from any notebook:

    import obs
    from lab_core.trace import Tracer

    obs.enable_mlflow()                          # dated experiment + pinned store
    tracer = Tracer(sinks=[obs.mlflow_sink()])   # lab spans -> MLflow traces
    obs.mlflow_ui()                              # find-or-start the UI; prints the link

    obs.enable_phoenix()                         # find-or-start Phoenix + OTel routing
    tracer = Tracer(sinks=[obs.phoenix_sink()])  # lab spans -> Phoenix traces

Design notes (the robustness contract, unchanged from dspy-lab):
- Sessions are dated: everything logs under ``agentic-lab-YYYY-MM-DD``, so work
  from different days never collides in the UIs.
- The MLflow store is pinned to ``mlflow.db`` at the repo root (not the cwd). If
  a remnant file is unusable — unwritable, corrupt, or not SQLite at all — a
  fresh dated store is used instead: leftover files can never break a session.
- Servers are reused when they are genuinely ours (health-checked), skipped when
  a stranger holds the port (the next port is tried), and started otherwise.
  Started servers are plain background processes: they survive kernel restarts,
  and rerunning a cell just finds them again.
"""

import datetime
import json
import os
import socket
import sqlite3
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

TODAY = datetime.date.today().isoformat()
EXPERIMENT = f"agentic-lab-{TODAY}"
ROOT = Path(__file__).resolve().parents[1]
_STORE_TAG = "agentic_lab.store"  # experiments are stamped with their store's absolute path

MLFLOW_DB: Path | None = None
_PHOENIX_PROVIDER = None


def _usable_sqlite(path: Path) -> bool:
    """True if MLflow could use the database at `path`: writable, and really SQLite."""
    try:
        conn = sqlite3.connect(path, timeout=2)
        try:
            conn.execute("BEGIN IMMEDIATE")  # wants write access + a valid header; changes nothing
            conn.rollback()
        finally:
            conn.close()
        return True
    except sqlite3.Error as exc:  # readonly, unopenable, corrupt, not-a-database, ...
        return "database is locked" in str(exc)  # ...but merely busy is a healthy store


def _store_path() -> Path:
    """Prefer the shared ./mlflow.db; fall back to a dated file if a remnant is unusable."""
    global MLFLOW_DB
    if MLFLOW_DB is None:
        default = ROOT / "mlflow.db"
        if _usable_sqlite(default):
            MLFLOW_DB = default
        else:
            MLFLOW_DB = ROOT / f"mlflow-{TODAY}.db"
            print(f"obs: {default.name} is not usable here; using {MLFLOW_DB.name} instead")
    return MLFLOW_DB


def _ensure_experiment():
    import mlflow

    store = str(_store_path())
    mlflow.set_tracking_uri(f"sqlite:///{store}")
    exp = mlflow.set_experiment(EXPERIMENT)
    if exp.tags.get(_STORE_TAG) != store:  # stamp the experiment with its store,
        mlflow.MlflowClient().set_experiment_tag(  # so a UI can prove which store it serves
            exp.experiment_id, _STORE_TAG, store
        )


def enable_mlflow():
    """Point MLflow at the dated experiment on the pinned, remnant-proof store."""
    _ensure_experiment()
    print(f"obs: MLflow ready — experiment {EXPERIMENT!r}, store {_store_path().name}")


def mlflow_sink():
    """A ``lab_core.trace`` sink that mirrors lab spans into MLflow traces, live."""
    import mlflow

    _ensure_experiment()

    class _MlflowSink:
        def __init__(self):
            self._live = {}

        def on_start(self, span):
            cm = mlflow.start_span(name=span.name)
            self._live[id(span)] = (cm, cm.__enter__())

        def on_end(self, span):
            cm, mlspan = self._live.pop(id(span))
            try:
                mlspan.set_attributes({k: str(v) for k, v in span.attributes.items()})
                if span.error:
                    mlspan.set_attribute("error", span.error)
            finally:
                cm.__exit__(None, None, None)

    return _MlflowSink()


def _port_open(port: int) -> bool:
    with socket.socket() as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def _http_get(url: str, timeout: float = 3.0) -> bytes | None:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return response.read(65536) if response.status == 200 else None
    except Exception:
        return None


def _find_or_start(name, start_on_port, is_ours, first_port, tries=4, wait_s=90):
    """Reuse a server that passes `is_ours`; skip ports held by strangers; else start one."""
    for port in range(first_port, first_port + tries):
        if _port_open(port):
            if is_ours(port):
                print(f"obs: {name} already running — http://127.0.0.1:{port}")
                return port
            continue  # someone else's server; try next port
        start_on_port(port)
        deadline = time.time() + wait_s
        while time.time() < deadline:
            if _port_open(port) and is_ours(port):
                print(f"obs: {name} — http://127.0.0.1:{port}")
                return port
            time.sleep(0.5)
        print(f"obs: {name} did not come up on port {port}; trying {port + 1}")
    print(f"obs: could not find or start {name} on ports {first_port}-{first_port + tries - 1}")
    return None


def _spawn(cmd, env=None):
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env, cwd=ROOT)


def mlflow_ui(port: int = 5000):
    """Find or start the MLflow UI on this lab's store; prints the link."""
    _ensure_experiment()  # the health check below needs it
    db = _store_path()

    def is_ours(p):  # ours = a UI serving OUR store: today's
        name = urllib.parse.quote(EXPERIMENT)  # experiment must exist there AND carry
        body = _http_get(
            f"http://127.0.0.1:{p}/api/2.0/mlflow/experiments/get-by-name?experiment_name={name}"
        )  # this store's path stamp — the name alone could be another checkout's
        if body is None:
            return False
        try:
            tags = json.loads(body)["experiment"].get("tags", [])
            return any(t.get("key") == _STORE_TAG and t.get("value") == str(db) for t in tags)
        except Exception:
            return False

    def start(p):
        _spawn(
            [
                sys.executable,
                "-m",
                "mlflow",
                "ui",
                "--backend-store-uri",
                f"sqlite:///{db}",
                "--port",
                str(p),
            ]
        )

    return _find_or_start("MLflow UI", start, is_ours, port)


def enable_phoenix(port: int = 6006):
    """Find or start Phoenix, then route this lab's OTel spans to the dated project."""
    global _PHOENIX_PROVIDER

    def is_ours(p):  # any healthy Phoenix will do:
        body = _http_get(f"http://127.0.0.1:{p}")  # instances share ~/.phoenix data
        return body is not None and b"phoenix" in body.lower()

    def start(p):
        _spawn(
            [sys.executable, "-m", "phoenix.server.main", "serve"],
            env={**os.environ, "PHOENIX_PORT": str(p)},
        )

    chosen = _find_or_start("Phoenix", start, is_ours, port)
    if chosen is not None:
        from phoenix.otel import register

        _PHOENIX_PROVIDER = register(
            project_name=EXPERIMENT, endpoint=f"http://127.0.0.1:{chosen}/v1/traces"
        )
        print(f"obs: Phoenix tracing on — project {EXPERIMENT!r}")
    return chosen


def phoenix_sink():
    """A ``lab_core.trace`` sink that mirrors lab spans into Phoenix via OpenTelemetry."""
    from opentelemetry import context as otel_context
    from opentelemetry import trace as otel_trace

    provider = _PHOENIX_PROVIDER or otel_trace.get_tracer_provider()
    tracer = provider.get_tracer("agentic-lab")

    class _PhoenixSink:
        def __init__(self):
            self._live = {}

        def on_start(self, span):
            otspan = tracer.start_span(span.name)
            token = otel_context.attach(otel_trace.set_span_in_context(otspan))
            self._live[id(span)] = (otspan, token)

        def on_end(self, span):
            otspan, token = self._live.pop(id(span))
            for key, value in span.attributes.items():
                otspan.set_attribute(key, str(value))
            if span.error:
                otspan.set_status(otel_trace.Status(otel_trace.StatusCode.ERROR, span.error))
            otel_context.detach(token)
            otspan.end()

    return _PhoenixSink()
