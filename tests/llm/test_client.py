from src.llm.client import LLMClient


def test_llm_client_defines_generate_contract():
    assert hasattr(LLMClient, "generate")
