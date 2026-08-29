"""Tests for the shared SMTP email tool (FR-901)."""

import logging
import smtplib
from pathlib import Path

import pytest
import yaml

from examples.shared.smtp_email import SmtpSendError, send_email
from yamlgraph.tools.manifest import ToolManifest

MANIFEST = (
    Path(__file__).parent.parent.parent / "examples" / "shared" / "smtp_email.tool.yaml"
)

SMTP_ENV = {
    "SMTP_SERVER": "mail.example.com",
    "SMTP_PORT": "587",
    "SMTP_USER": "sender@example.com",
    "SMTP_PASSWORD": "hunter2-secret",
    "SMTP_TO": "recipient@example.com",
}


class FakeSMTP:
    """Recording double standing in for smtplib.SMTP / SMTP_SSL."""

    instances: list["FakeSMTP"] = []

    def __init__(self, host, port, timeout=None):
        self.host = host
        self.port = port
        self.started_tls = False
        self.logged_in = None
        self.sent = []
        self.send_error = None
        FakeSMTP.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def starttls(self):
        self.started_tls = True

    def login(self, user, password):
        self.logged_in = (user, password)

    def send_message(self, msg):
        if self.send_error:
            raise self.send_error
        self.sent.append(msg)


@pytest.fixture(autouse=True)
def _reset_fake():
    FakeSMTP.instances = []
    yield
    FakeSMTP.instances = []


@pytest.fixture
def smtp_env(monkeypatch):
    for key, value in SMTP_ENV.items():
        monkeypatch.setenv(key, value)
    monkeypatch.delenv("SMTP_FROM", raising=False)


def call(**kwargs):
    kwargs.setdefault("subject", "Subject")
    kwargs.setdefault("text", "Body")
    kwargs.setdefault("smtp_factory", FakeSMTP)
    kwargs.setdefault("smtp_ssl_factory", FakeSMTP)
    return send_email(**kwargs)


@pytest.mark.req("REQ-YG-627")
class TestManifest:
    def test_manifest_validates_as_python_runtime_tool(self):
        raw = yaml.safe_load(MANIFEST.read_text())
        manifest = ToolManifest.model_validate(raw)

        assert manifest.name == "send_email"
        assert manifest.runtime.type == "python"
        assert manifest.runtime.module == "examples.shared.smtp_email"
        assert manifest.runtime.function == "send_email"

    def test_manifest_names_its_first_consumer(self):
        assert "First consumer:" in MANIFEST.read_text()


@pytest.mark.req("REQ-YG-627")
class TestConfigValidation:
    def test_missing_config_names_every_key_at_once(self, monkeypatch):
        for key in SMTP_ENV:
            monkeypatch.delenv(key, raising=False)

        with pytest.raises(SmtpSendError) as exc:
            call()

        message = str(exc.value)
        for key in ("SMTP_SERVER", "SMTP_PORT", "SMTP_USER", "SMTP_PASSWORD"):
            assert key in message
        assert not FakeSMTP.instances, "no socket may be opened before validation"

    def test_missing_recipient_raises(self, smtp_env, monkeypatch):
        monkeypatch.delenv("SMTP_TO")

        with pytest.raises(SmtpSendError, match="recipient"):
            call()

        assert not FakeSMTP.instances

    def test_credentials_are_read_at_call_time(self, smtp_env, monkeypatch):
        monkeypatch.setenv("SMTP_USER", "late@example.com")

        call()

        assert FakeSMTP.instances[0].logged_in[0] == "late@example.com"


@pytest.mark.req("REQ-YG-627")
class TestTransportSelection:
    def test_port_465_uses_implicit_tls_without_starttls(self, smtp_env, monkeypatch):
        monkeypatch.setenv("SMTP_PORT", "465")
        ssl_calls = []

        def ssl_factory(host, port, timeout=None):
            ssl_calls.append((host, port))
            return FakeSMTP(host, port, timeout)

        call(smtp_ssl_factory=ssl_factory, smtp_factory=_forbidden_factory)

        assert ssl_calls == [("mail.example.com", 465)]
        assert FakeSMTP.instances[0].started_tls is False

    def test_other_port_uses_starttls(self, smtp_env):
        call()

        assert FakeSMTP.instances[0].started_tls is True
        assert FakeSMTP.instances[0].port == 587


@pytest.mark.req("REQ-YG-627")
class TestMessageShape:
    def test_text_only_has_single_part(self, smtp_env):
        call(text="plain body")

        msg = FakeSMTP.instances[0].sent[0]
        assert not msg.is_multipart()
        assert msg.get_content().strip() == "plain body"

    def test_html_produces_alternative_with_nonempty_text(self, smtp_env):
        call(text="plain body", html="<p>rich</p>")

        msg = FakeSMTP.instances[0].sent[0]
        assert msg.get_content_subtype() == "alternative"
        text_part = msg.get_body(preferencelist=("plain",))
        assert text_part.get_content().strip() == "plain body"
        assert msg.get_body(preferencelist=("html",)) is not None

    def test_recipients_accept_single_and_comma_list(self, smtp_env):
        result = call(to="a@example.com, b@example.com", cc="c@example.com")

        msg = FakeSMTP.instances[0].sent[0]
        assert msg["To"] == "a@example.com, b@example.com"
        assert msg["Cc"] == "c@example.com"
        assert result["to"] == ["a@example.com", "b@example.com", "c@example.com"]

    def test_smtp_from_overrides_sender_header(self, smtp_env, monkeypatch):
        monkeypatch.setenv("SMTP_FROM", "Digest <noreply@example.com>")

        call()

        assert FakeSMTP.instances[0].sent[0]["From"] == "Digest <noreply@example.com>"


@pytest.mark.req("REQ-YG-627")
class TestAttachments:
    def test_present_file_is_attached_with_guessed_type(self, smtp_env, tmp_path):
        report = tmp_path / "digest.md"
        report.write_text("# report\n")

        call(attachments=[str(report)])

        msg = FakeSMTP.instances[0].sent[0]
        names = [part.get_filename() for part in msg.iter_attachments()]
        assert names == ["digest.md"]

    def test_missing_attachment_raises_before_connecting(self, smtp_env, tmp_path):
        with pytest.raises(SmtpSendError, match="attachment"):
            call(attachments=[str(tmp_path / "absent.md")])

        assert not FakeSMTP.instances


@pytest.mark.req("REQ-YG-627")
class TestHeaderInjection:
    @pytest.mark.parametrize(
        "field,value",
        [
            ("subject", "Digest\nBcc: victim@example.com"),
            ("to", "a@example.com\rBcc: victim@example.com"),
            ("cc", "c@example.com\nBcc: victim@example.com"),
        ],
    )
    def test_crlf_in_headers_is_refused(self, smtp_env, field, value):
        with pytest.raises(SmtpSendError, match="line break"):
            call(**{field: value})

        assert not FakeSMTP.instances


@pytest.mark.req("REQ-YG-627")
class TestFailureDisclosure:
    def test_send_failure_propagates_as_raise(self, smtp_env):
        def failing_factory(host, port, timeout=None):
            fake = FakeSMTP(host, port, timeout)
            fake.send_error = smtplib.SMTPRecipientsRefused({})
            return fake

        with pytest.raises(SmtpSendError):
            call(smtp_factory=failing_factory)

    def test_password_never_reaches_logs_or_exception(self, smtp_env, caplog):
        def failing_factory(host, port, timeout=None):
            fake = FakeSMTP(host, port, timeout)
            fake.send_error = smtplib.SMTPAuthenticationError(
                535, b"auth failed for hunter2-secret"
            )
            return fake

        with caplog.at_level(logging.DEBUG), pytest.raises(SmtpSendError) as exc:
            call(smtp_factory=failing_factory)

        assert "hunter2-secret" not in str(exc.value)
        assert exc.value.__cause__ is None, "raw smtplib error must not be chained"
        assert "hunter2-secret" not in caplog.text


def _forbidden_factory(*args, **kwargs):
    raise AssertionError("plaintext SMTP factory must not be used on port 465")
