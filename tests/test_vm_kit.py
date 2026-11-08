"""No hostile sites/VMs used: policy, loopback broker and PowerShell control-flow checks."""

import base64
import copy
import json
import socket
import subprocess
import sys
import threading
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

import pytest

from vm_kit.broker import Broker
from vm_kit.explanations import FLAGS, permitted, selection, summary, validate_report
from vm_kit.policy import PolicyError, PublicPolicy, target_origin

ROOT = Path(__file__).resolve().parent.parent
TOKEN = "synthetic-test-session-token-with-32-characters"


def report():
    return {
        "version": 1,
        "status": "done",
        "flags": dict.fromkeys(FLAGS, False),
        "template_ids": ["no_observed_flags"],
        "ai_status": "not_requested",
        "observed_requests": 1,
        "blocked_requests": 0,
    }


@pytest.mark.parametrize(
    "value",
    [
        "http://localhost",
        "http://127.0.0.1",
        "http://169.254.169.254",
        "http://10.0.0.1",
        "http://224.0.0.1",
        "http://239.1.1.1",
        "http://[::1]",
        "http://[2606:4700:4700::1111]",
        "https://user:pass@example.com",
        "https://example.com/login",
        "https://example.com/?token=private",
        "https://example.com/#x",
        "file:///C:/Windows",
        "https://example.com:8443",
        "https://foo.local",
        "http://2130706433",
        "https://evil.example",
    ],
)
def test_vm_target_rejects_private_or_non_origin(value):
    with pytest.raises(PolicyError):
        target_origin(value)


def test_vm_origin_canonicalization():
    assert target_origin("https://EXAMPLE.com/") == "https://example.com"


@pytest.mark.parametrize(
    "answers",
    [
        ["127.0.0.1"],
        ["169.254.169.254"],
        ["224.0.0.1"],
        ["239.1.1.1"],
        ["93.184.216.34", "10.0.0.1"],
        ["192.0.2.1"],
        ["0.0.0.0"],
    ],
)
def test_vm_all_dns_answers_must_be_public(answers):
    rows = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, 443)) for ip in answers]
    with (
        patch("vm_kit.policy.socket.getaddrinfo", return_value=rows),
        pytest.raises(PolicyError),
    ):
        PublicPolicy().resolve("example.com", 443)


def test_vm_dns_is_pinned_and_connected_public_subnets_are_denied():
    rows = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))]
    sentinel = object()
    with (
        patch("vm_kit.policy.socket.getaddrinfo", return_value=rows) as resolve,
        patch(
            "vm_kit.policy.socket.create_connection", return_value=sentinel
        ) as connect,
    ):
        assert PublicPolicy().connect("example.com", 443) is sentinel
        resolve.assert_called_once()
        connect.assert_called_once_with(("93.184.216.34", 443), timeout=5)
        with pytest.raises(PolicyError):
            PublicPolicy(["93.184.216.0/24"]).resolve("example.com", 443)
        with pytest.raises(PolicyError):
            PublicPolicy(["93.184.216.34/32"]).resolve("example.com", 443)


@contextmanager
def running_broker(tmp_path):
    broker = Broker(
        ("127.0.0.1", 0),
        TOKEN,
        result_path=tmp_path / "result.json",
        start_path=tmp_path / "start.signal",
    )
    thread = threading.Thread(target=broker.serve_forever, daemon=True)
    thread.start()
    try:
        yield broker
    finally:
        broker.shutdown()
        broker.server_close()
        thread.join(timeout=2)


def request(broker, method, target, body=b"", auth=True, extra=""):
    header = (
        "Proxy-Authorization: Basic "
        + base64.b64encode(("tdefense:" + TOKEN).encode()).decode()
        + "\r\n"
        if auth
        else ""
    )
    data = (
        f"{method} {target} HTTP/1.1\r\n{header}Content-Length: {len(body)}\r\n{extra}\r\n".encode()
        + body
    )
    with socket.create_connection(broker.server_address, timeout=2) as client:
        client.settimeout(2)
        client.sendall(data)
        chunks = []
        while True:
            value = client.recv(65536)
            if not value:
                break
            chunks.append(value)
    return b"".join(chunks)


def test_vm_broker_authentication_and_no_private_connect(tmp_path):
    with running_broker(tmp_path) as broker:
        with patch.object(broker.policy, "connect") as connect:
            assert request(broker, "CONNECT", "example.com:443", auth=False).startswith(
                b"HTTP/1.1 407"
            )
            assert b"Proxy-Authenticate: Basic" in request(
                broker, "CONNECT", "example.com:443", auth=False
            )
            connect.assert_not_called()
        assert request(broker, "CONNECT", "127.0.0.1:443").startswith(b"HTTP/1.1 403")
        assert request(broker, "CONNECT", "224.0.0.1:443").startswith(b"HTTP/1.1 403")
        assert request(broker, "CONNECT", "example.com:8000").startswith(
            b"HTTP/1.1 403"
        )
        assert request(broker, "POST", "http://example.com/").startswith(
            b"HTTP/1.1 403"
        )


def test_vm_report_transport_is_authenticated_bounded_and_one_shot(tmp_path):
    with running_broker(tmp_path) as broker:
        valid = json.dumps(report()).encode()
        assert request(broker, "POST", "/__tdefense_result", valid).startswith(
            b"HTTP/1.1 403"
        )
        (tmp_path / "start.signal").touch()
        assert request(broker, "GET", "/__tdefense_ready", auth=False).startswith(
            b"HTTP/1.1 407"
        )
        assert b'"ready": true' in request(broker, "GET", "/__tdefense_ready")
        bad = report()
        bad["verdict"] = "safe"
        assert request(
            broker, "POST", "/__tdefense_result", json.dumps(bad).encode()
        ).startswith(b"HTTP/1.1 403")
        assert not (tmp_path / "result.json").exists()
        assert request(
            broker, "POST", "/__tdefense_result", valid, auth=False
        ).startswith(b"HTTP/1.1 407")
        # An oversized declared length is rejected before reading the body.
        with socket.create_connection(broker.server_address, timeout=2) as client:
            auth = base64.b64encode(("tdefense:" + TOKEN).encode()).decode()
            client.sendall(
                f"POST /__tdefense_result HTTP/1.1\r\nProxy-Authorization: Basic {auth}\r\nContent-Length: 65537\r\n\r\n".encode()
            )
            assert client.recv(1024).startswith(b"HTTP/1.1 403")
        assert request(broker, "POST", "/__tdefense_result", valid).startswith(
            b"HTTP/1.1 201"
        )
        assert json.loads((tmp_path / "result.json").read_text()) == report()
        assert request(broker, "POST", "/__tdefense_result", valid).startswith(
            b"HTTP/1.1 403"
        )


def test_vm_http_proxy_strips_credentials_and_pins_upstream(tmp_path):
    left, right = socket.socketpair()
    observed = []

    def upstream():
        with right:
            data = right.recv(16384)
            observed.append(data)
            right.sendall(
                b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\nConnection: close\r\n\r\nOK"
            )

    with (
        running_broker(tmp_path) as broker,
        patch.object(broker.policy, "connect", return_value=left) as connect,
    ):
        (tmp_path / "start.signal").touch()
        thread = threading.Thread(target=upstream, daemon=True)
        thread.start()
        result = request(
            broker,
            "GET",
            "http://example.com/check?sample=synthetic",
            extra="Cookie: private-cookie\r\nAuthorization: Bearer private-token\r\n",
        )
        thread.join(timeout=2)
        assert result.endswith(b"OK")
        connect.assert_called_once_with("example.com", 80)
    assert b"GET /check?sample=synthetic" in observed[0]
    assert (
        b"private-cookie" not in observed[0]
        and b"private-token" not in observed[0]
        and TOKEN.encode() not in observed[0]
    )


def test_vm_ai_cannot_invent_flags_or_hide_observed_evidence():
    value = report()
    value["flags"]["password_request"] = True
    value["flags"]["cross_origin_form"] = True
    value["template_ids"] = ["password_request"]
    assert len(summary(value)) == 2
    with pytest.raises(ValueError):
        selection({"template_ids": ["safe"]}, value["flags"])
    with pytest.raises(ValueError):
        selection({"template_ids": ["download_attempt"]}, value["flags"])
    with pytest.raises(ValueError):
        selection(
            {"template_ids": ["password_request"], "raw_text": "ignore rules"},
            value["flags"],
        )
    assert permitted(report()["flags"]) == ["no_observed_flags"]


@pytest.mark.parametrize(
    "change",
    [
        {"version": True},
        {"observed_requests": 0},
        {"blocked_requests": 1},
        {"ai_status": "unavailable"},
        {"verdict": "safe"},
        {"observed_requests": True},
    ],
)
def test_vm_contradictory_reports_rejected(change):
    value = copy.deepcopy(report())
    value.update(change)
    with pytest.raises(ValueError):
        validate_report(value)


def test_vm_worker_refuses_accidental_host_execution(monkeypatch):
    from vm_kit.worker import inspect

    monkeypatch.delenv("TDEFENSE_DISPOSABLE_GUEST", raising=False)
    with pytest.raises(RuntimeError):
        inspect({})


def test_vm_control_script_parses_and_preflight_is_non_mutating():
    if sys.platform != "win32":
        pytest.skip("Windows PowerShell syntax/runtime preflight")
    script = ROOT / "vm_kit/TDefense-VM.ps1"
    command = "$e=@();[System.Management.Automation.Language.Parser]::ParseFile($args[0],[ref]$null,[ref]$e)|Out-Null;if($e.Count){$e|ForEach-Object Message;exit 1}"
    # Parse via a literal path; no untrusted strings enter PowerShell command text.
    escaped = str(script).replace("'", "''")
    parsed = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-Command",
            command.replace("$args[0]", "'" + escaped + "'"),
        ],
        capture_output=True,
        check=False,
        text=True,
        timeout=20,
    )
    assert parsed.returncode == 0, parsed.stdout + parsed.stderr
    probe = subprocess.run(
        ["powershell.exe", "-NoProfile", "-File", str(script), "-Action", "Preflight"],
        capture_output=True,
        check=False,
        text=True,
        timeout=20,
    )
    assert probe.returncode == 0, probe.stderr
    result = json.loads(probe.stdout)
    assert result["LiveReady"] is False
    text = script.read_text(encoding="utf8")
    assert text.index("Assert-Acls $jobVM") < text.index(
        "Connect-VMNetworkAdapter -VMName $jobVM"
    )
    assert text.index("Remove-PSSession $session;$session=$null") < text.index(
        "New-Item -ItemType File -Path $startPath"
    )
    assert "New-NetNat" not in text and "ExternalSwitch" not in text


def test_vm_egress_cannot_open_before_host_release(tmp_path):
    with (
        running_broker(tmp_path) as broker,
        patch.object(broker.policy, "connect") as connect,
    ):
        assert request(broker, "CONNECT", "example.com:443").startswith(b"HTTP/1.1 403")
        assert request(broker, "GET", "http://example.com/").startswith(b"HTTP/1.1 403")
        connect.assert_not_called()


@pytest.mark.parametrize("scenario", ["plain", "submit", "frame", "many_forms"])
def test_vm_readonly_worker_with_real_chromium_and_fully_intercepted_synthetic_page(
    monkeypatch, scenario
):
    from types import SimpleNamespace

    from playwright.sync_api import Browser, BrowserType

    from vm_kit.worker import inspect

    monkeypatch.setenv("TDEFENSE_DISPOSABLE_GUEST", "1")
    launch = BrowserType.launch
    make_context = Browser.new_context
    observed = []
    html = '<html><form action="https://other.example.com/collect"><input type="password"></form>'
    if scenario == "submit":
        html += '<script>fetch("/write",{method:"POST",body:"SYNTHETIC"}).catch(()=>{});</script>'

    if scenario == "frame":
        html += '<script>let f=document.createElement("iframe");f.srcdoc="<p>Synthetic transient frame</p>";document.body.append(f);setTimeout(()=>f.remove(),100);</script>'
    if scenario == "many_forms":
        html += "<form></form>" * 31

    def test_launch(self, **kwargs):
        # Test-only substitution: actual VM/proxy is unavailable. All requests are fulfilled below.
        kwargs.pop("proxy", None)
        # Codex host app restrictions prevent nested Chromium OS sandboxing here.
        # Production worker and guest sealing still require chromium_sandbox=True.
        kwargs["chromium_sandbox"] = False
        kwargs["args"] = [
            x
            for x in kwargs.get("args", [])
            if not x.startswith("--host-resolver-rules")
        ]
        return launch(self, **kwargs)

    def test_context(self, **kwargs):
        context = make_context(self, **kwargs)
        register = context.route

        def route(pattern, handler):
            def intercepted(real):
                observed.append(real.request.method)
                handler(
                    SimpleNamespace(
                        request=real.request,
                        continue_=lambda: real.fulfill(
                            status=200, content_type="text/html", body=html
                        ),
                        abort=real.abort,
                    )
                )

            return register(pattern, intercepted)

        context.route = route
        return context

    monkeypatch.setattr(BrowserType, "launch", test_launch)
    monkeypatch.setattr(Browser, "new_context", test_context)
    value = inspect(
        {
            "target_origin": "https://example.com",
            "proxy": "http://192.168.253.1:18080",
            "token": TOKEN,
        }
    )
    assert value["flags"]["password_request"] and value["flags"]["cross_origin_form"]
    assert value["status"] == ("done" if scenario == "plain" else "inconclusive")
    assert bool(value["blocked_requests"]) is (scenario == "submit")
    assert value["ai_status"] == "not_requested"
    assert "<html>" not in json.dumps(value) and "https://" not in json.dumps(value)
    assert "POST" in observed if scenario == "submit" else observed == ["GET"]


def test_vm_local_model_receives_only_flags_and_returns_validated_ids(monkeypatch):
    from contextlib import nullcontext

    from vm_kit.worker import local_ai

    flags = dict.fromkeys(FLAGS, False)
    flags["password_request"] = True
    captured = []

    class FakeOpener:
        def open(self, request, timeout):
            captured.append(json.loads(request.data))
            assert request.full_url == "http://127.0.0.1:11434/api/generate"
            return nullcontext(
                type(
                    "Response",
                    (),
                    {
                        "read": lambda self, n: json.dumps(
                            {"response": '{"template_ids":["password_request"]}'}
                        ).encode()
                    },
                )()
            )

    monkeypatch.setattr(
        "vm_kit.worker.urllib.request.build_opener", lambda *args: FakeOpener()
    )
    assert local_ai(flags) == ["password_request"]
    assert captured[0]["options"]["num_gpu"] == 0 and captured[0]["stream"] is False
    assert (
        "https://" not in captured[0]["prompt"]
        and "<html>" not in captured[0]["prompt"]
    )


def test_vm_acl_readback_rejects_tampered_real_powershell_objects():
    if sys.platform != "win32":
        pytest.skip("Windows PowerShell ACL-verifier behavior")
    script = str(ROOT / "vm_kit/TDefense-VM.ps1").replace("'", "''")
    command = r"""
$ErrorActionPreference='Stop'
$text=Get-Content -LiteralPath 'SCRIPT' -Raw
$start=$text.IndexOf('function Assert-Acls')
$end=$text.IndexOf('function Guest-Session',$start)
. ([ScriptBlock]::Create($text.Substring($start,$end-$start)))
$hostAddress='192.168.253.1'
function Get-VMNetworkAdapterExtendedAcl { param($VMName);return $script:rules }
function Rules {
 $script:rules=@()
 foreach ($e in @(@(1,'Outbound','0.0.0.0/0'),@(2,'Outbound','::/0'),@(3,'Inbound','0.0.0.0/0'),@(4,'Inbound','::/0'))) {
  $script:rules += [pscustomobject]@{Weight=$e[0];Direction=$e[1];RemoteIPAddress=$e[2];Action='Deny';Stateful=$false;LocalIPAddress='';RemotePort='';LocalPort='';Protocol='Any'}
 }
 $script:rules += [pscustomobject]@{Weight=100;Direction='Outbound';RemoteIPAddress=$hostAddress;RemotePort='18080';Protocol='TCP';Action='Allow';Stateful=$true;IdleSessionTimeout=90}
}
Rules
Assert-Acls 'synthetic'
$mutations=@(@(0,'Action','Allow'),@(1,'RemoteIPAddress','::1/128'),@(2,'LocalIPAddress','192.168.253.2/32'),@(3,'Protocol','TCP'),@(4,'RemotePort','443'),@(4,'Stateful',$false),@(4,'Direction','Inbound'),@(4,'Weight',99))
foreach ($m in $mutations) {
 Rules
 $rules[$m[0]].($m[1])=$m[2]
 $rejected=$false
 try {Assert-Acls 'synthetic'} catch {$rejected=$true}
 if (-not $rejected) {throw 'Tampered ACL accepted'}
}
'OK'
""".replace("SCRIPT", script)
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-Command", command],
        capture_output=True,
        text=True,
        check=False,
        timeout=20,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "OK" in result.stdout
