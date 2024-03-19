from jsonref import requests
from pytest_asyncio import fixture

from eidolon_ai_client.client import Machine


@fixture(scope="module", autouse=True)
def http_server(eidolon_server, eidolon_examples):
    with eidolon_server(eidolon_examples / "hello_world" / "resources", log_file="hello_world_log.txt") as server:
        yield server


def test_server_is_running(server_loc):
    response = requests.get(f"{server_loc}/openapi.json")
    assert response.status_code == 200
    assert "/processes/{process_id}/agent/ExampleGeneric/actions/question" in response.json()["paths"]


async def test_can_hit_generic_agent(server_loc):
    process = await Machine(machine=server_loc).agent("ExampleGeneric").create_process()
    response = await process.action("question", json=dict(instruction="Hi! What is the capital of France?"))
    assert "paris" in response.data.lower()


async def test_tool_calls(server_loc):
    process = await Machine(machine=server_loc).agent("ExampleGeneric").create_process()
    await process.action("question", json=dict(instruction="Hi! My name is Luke."))
    response = await process.action("respond", json=dict(statement="Please use the HelloWorld tool with my name."))
    assert "Luke" in response.data
