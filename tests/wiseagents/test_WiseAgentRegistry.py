import logging

import pytest

from wiseagents import WiseAgent, WiseAgentContext, WiseAgentMessage, WiseAgentRegistry, WiseAgentTransport
from wiseagents.transports.stomp import StompWiseAgentTransport


@pytest.fixture(scope="session", autouse=True)
def run_after_all_tests():
    yield
    

class TestAgent(WiseAgent):
    def __init__(self, name, description, transport):
        super().__init__(name, description, transport)
        self._started = False
        self._stopped = False

class DummyTransport(WiseAgentTransport):
    
    def send_request(self, message: WiseAgentMessage, dest_agent_name: str):
        return super().send_request(message, dest_agent_name)
        pass
    def send_response(self, message: WiseAgentMessage, dest_agent_name: str):
        pass
    def start(self):
        pass
    def stop(self):
        pass
   
def test_register_agents():
    
    try:
        agent = TestAgent(name="Agent1", description="This is a test agent",
                      transport=StompWiseAgentTransport(host='localhost', port=61616, agent_name="WiseIntelligentAgent")
                                 )
        assert 1 == WiseAgentRegistry.fetch_agents_descriptions_dict().__len__()
        logging.info(f'Agent ={agent}')
        logging.info(f'Agent in the registry={WiseAgentRegistry.get_agent_description(agent.name)}')
        assert agent.description == WiseAgentRegistry.get_agent_description(agent.name)
    finally:    
        agent.stop_agent()

def test_get_agents():
    try:
        agents = [TestAgent(name="Agent1", description="This is a test agent", transport=DummyTransport()),
                TestAgent(name="Agent2", description="This is another test agent", transport=DummyTransport()),
                TestAgent(name="Agent3", description="This is yet another test agent", transport=DummyTransport())]
        
        for agent in agents:
            assert agent.description == WiseAgentRegistry.get_agent_description(agent.name)
        #stop the agents
    finally:
        for agent in agents:
            agent.stop_agent()

def test_get_contexts():
    
    contexts = [WiseAgentContext(name="Context1"), 
              WiseAgentContext(name="Context2"), 
              WiseAgentContext(name="Context3")]
    
    for context in contexts:
        assert True == WiseAgentRegistry.does_context_exist(context.name)
        
def test_get_or_create_context():
    
    context = WiseAgentContext(name="Context1")
    WiseAgentRegistry.get_or_create_context(context.name)
    assert context == WiseAgentRegistry.get_or_create_context(context.name)