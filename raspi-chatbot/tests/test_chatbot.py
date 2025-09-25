from src.chatbot.convo_manager import ConvoManager
from src.chatbot.state_store import StateStore
from src.services.github_model_client import GitHubModelClient

def test_convo_manager_initialization():
    convo_manager = ConvoManager()
    assert convo_manager is not None

def test_convo_manager_response():
    convo_manager = ConvoManager()
    response = convo_manager.process_input("Hello")
    assert response is not None
    assert isinstance(response, str)

def test_state_store_save_load():
    state_store = StateStore()
    test_state = {"user_input": "Hello", "bot_response": "Hi there!"}
    state_store.save_state(test_state)
    loaded_state = state_store.load_state()
    assert loaded_state == test_state

def test_github_model_client_request():
    client = GitHubModelClient()
    response = client.get_response("Hello")
    assert response is not None
    assert isinstance(response, str)