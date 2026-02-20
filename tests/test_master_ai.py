# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
import unittest
from swarmz_runtime.orchestrator.orchestrator import Crew, Agent, Task, crew_from_config
from unittest.mock import patch

class TestMasterAI(unittest.TestCase):

    def setUp(self):
        self.agents = [
            Agent(name="Agent1", role="Explorer", goal="Explore new territories."),
            Agent(name="Agent2", role="Analyzer", goal="Analyze collected data."),
        ]

        self.tasks = [
            Task(name="Task1", description="Explore the forest.", expected_output="Map of the forest.", agent_name="Agent1"),
            Task(name="Task2", description="Analyze the soil samples.", expected_output="Soil composition report.", agent_name="Agent2"),
        ]

        self.crew = Crew(agents=self.agents, tasks=self.tasks)

    @patch("swarmz_runtime.orchestrator.orchestrator.OpenAIResponsesClient")
    def test_master_ai_simulation(self, MockLLM):
        """Test Master SWARM AI in simulation mode (no API key)."""
        # Mock the OpenAIResponsesClient to simulate disabled state
        MockLLM.return_value.enabled.return_value = False
        self.crew.llm = MockLLM()

        result = self.crew.master_ai("Understand the ecosystem.")
        self.assertEqual(len(result.outputs), 1)
        self.assertIn("[SIMULATED]", result.outputs[0]["result"])

    def test_master_ai_real(self):
        """Test Master SWARM AI with real API calls (requires API key)."""
        if not self.crew.llm.enabled():
            self.skipTest("OpenAI API key not set.")

        result = self.crew.master_ai("Understand the ecosystem.")
        self.assertEqual(len(result.outputs), 1)
        self.assertIn("result", result.outputs[0])
        self.assertNotIn("error", result.outputs[0])

if __name__ == "__main__":
    unittest.main()
