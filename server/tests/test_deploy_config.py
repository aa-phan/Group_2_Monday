"""The deploy config gives the server every setting it needs (TD-08).

render.yaml is plain config, so nothing fails at build time if a
required setting goes missing; the app just misbehaves once it's live.
SECRET_KEY is the sharp one: without it each gunicorn worker invents its
own key and signed-in users are randomly treated as signed out. These
tests read the files directly so that a missing setting fails here
instead of in front of a grader.
"""

import pathlib
import re

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


def _renderEnvKeys():
    text = (REPO_ROOT / "render.yaml").read_text()
    return set(re.findall(r"^\s*-\s*key:\s*([A-Z_]+)\s*$", text, flags=re.MULTILINE))


def test_render_sets_the_database_connection_string():
    assert "MONGODB_URI" in _renderEnvKeys()


def test_render_sets_a_session_secret():
    assert "SECRET_KEY" in _renderEnvKeys()


def test_render_generates_the_session_secret_instead_of_committing_one():
    text = (REPO_ROOT / "render.yaml").read_text()
    block = re.search(r"-\s*key:\s*SECRET_KEY\s*\n((?:\s+\S.*\n?)*)", text)
    assert block is not None
    assert "generateValue: true" in block.group(1)
    assert "value:" not in block.group(1).replace("generateValue:", "")


def test_env_example_documents_every_render_setting():
    """A teammate setting up locally sees the same settings production uses."""
    example = (REPO_ROOT / ".env.example").read_text()
    for key in _renderEnvKeys():
        assert re.search(r"^{}=".format(key), example, flags=re.MULTILINE), key
