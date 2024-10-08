import logging
import os
import threading

import pytest

from wiseagents import WiseAgentMessage, WiseAgentRegistry
from wiseagents.agents import LLMOnlyWiseAgent, PassThroughClientAgent, SequentialCoordinatorWiseAgent
from wiseagents.llm import OpenaiAPIWiseAgentLLM
from wiseagents.transports import StompWiseAgentTransport

cond = threading.Condition()

assertError : AssertionError = None

@pytest.fixture(scope="session", autouse=True)
def run_after_all_tests():
    yield
    
    

def response_delivered(message: WiseAgentMessage):
    global assertError
    with cond:
        response = message.message

        try:
            assert "Agent0" in response
            assert "Agent1" in response
            assert "Agent2" in response
        except AssertionError:
            logging.info(f"assertion failed")
            assertError = AssertionError
        cond.notify()


def test_sequential_coordinator():
    """
    Requires STOMP_USER and STOMP_PASSWORD.
    """
    try:
        global assertError
        groq_api_key = os.getenv("GROQ_API_KEY")
        
        llm1 = OpenaiAPIWiseAgentLLM(system_message="Your name is Agent1. Answer my greeting saying Hello and my name and tell me your name.",
                                    model_name="llama-3.1-70b-versatile", remote_address="https://api.groq.com/openai/v1",
                                    api_key=groq_api_key)
        agent1 = LLMOnlyWiseAgent(name="Agent1", description="This is a test agent", llm=llm1,
                                transport=StompWiseAgentTransport(host='localhost', port=61616, agent_name="Agent1"))

        llm2 = OpenaiAPIWiseAgentLLM(system_message="Your name is Agent2. Answer my greeting saying Hello and include all agent names from the given message and tell me your name.",
                                    model_name="llama-3.1-70b-versatile", remote_address="https://api.groq.com/openai/v1",
                                    api_key=groq_api_key)
        agent2 = LLMOnlyWiseAgent(name="Agent2", description="This is a test agent", llm=llm2,
                                transport=StompWiseAgentTransport(host='localhost', port=61616, agent_name="Agent2"))

        coordinator = SequentialCoordinatorWiseAgent(name="SequentialCoordinator", description="This is a coordinator agent",
                                                    transport=StompWiseAgentTransport(host='localhost', port=61616, agent_name="SequentialCoordinator"),
                                                    agents=["Agent1", "Agent2"])

        with cond:
            client_agent1 = PassThroughClientAgent(name="PassThroughClientAgent1", description="This is a test agent",
                                                transport=StompWiseAgentTransport(host='localhost', port=61616, agent_name="PassThroughClientAgent1")
                                                )
            client_agent1.set_response_delivery(response_delivered)
            client_agent1.send_request(WiseAgentMessage("My name is Agent0", "PassThroughClientAgent1"),
                                    "SequentialCoordinator")
            cond.wait()
            if assertError is not None:
                logging.info(f"assertion failed")
                raise assertError
            logging.debug(f"registered agents= {WiseAgentRegistry.fetch_agents_descriptions_dict()}")
            for message in WiseAgentRegistry.get_or_create_context('default').message_trace:
                logging.debug(f'{message}')
    finally:
        #stop all agents
        client_agent1.stop_agent()
        agent1.stop_agent()
        agent2.stop_agent()
        coordinator.stop_agent()

