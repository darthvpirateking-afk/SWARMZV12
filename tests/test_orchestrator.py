import unittest
from unittest.mock import patch, MagicMock
from kernel_runtime.orchestrator import SwarmzOrchestrator

class TestSwarmzOrchestrator(unittest.TestCase):

    def setUp(self):
        self.orchestrator = SwarmzOrchestrator()

    @patch("kernel_runtime.orchestrator.SwarmzOrchestrator.load_mesh")
    @patch("kernel_runtime.orchestrator.SwarmzOrchestrator.start_governor")
    @patch("kernel_runtime.orchestrator.SwarmzOrchestrator.start_patchpack")
    @patch("kernel_runtime.orchestrator.SwarmzOrchestrator.start_session")
    @patch("kernel_runtime.orchestrator.SwarmzOrchestrator.start_mission_engine")
    @patch("kernel_runtime.orchestrator.SwarmzOrchestrator.start_swarm_engine")
    @patch("kernel_runtime.orchestrator.SwarmzOrchestrator.start_avatar")
    @patch("kernel_runtime.orchestrator.SwarmzOrchestrator.start_api")
    @patch("kernel_runtime.orchestrator.SwarmzOrchestrator.launch_cockpit")
    def test_activate(self, mock_launch_cockpit, mock_start_api, mock_start_avatar, mock_start_swarm_engine,
                      mock_start_mission_engine, mock_start_session, mock_start_patchpack, mock_start_governor,
                      mock_load_mesh):
        # Mock return values
        mock_load_mesh.return_value = MagicMock()
        mock_start_governor.return_value = MagicMock()
        mock_start_patchpack.return_value = MagicMock()
        mock_start_session.return_value = MagicMock()
        mock_start_mission_engine.return_value = MagicMock()
        mock_start_swarm_engine.return_value = MagicMock()
        mock_start_avatar.return_value = MagicMock()
        mock_start_api.return_value = None
        mock_launch_cockpit.return_value = MagicMock()

        # Call activate
        self.orchestrator.activate()

        # Assert all subsystems were started
        mock_load_mesh.assert_called_once()
        mock_start_governor.assert_called_once()
        mock_start_patchpack.assert_called_once()
        mock_start_session.assert_called_once()
        mock_start_mission_engine.assert_called_once()
        mock_start_swarm_engine.assert_called_once()
        mock_start_avatar.assert_called_once()
        mock_start_api.assert_called_once()
        mock_launch_cockpit.assert_called_once()

    def test_load_config(self):
        config = self.orchestrator.load_config()
        self.assertIsInstance(config, dict)
        self.assertEqual(config, {})

if __name__ == "__main__":
    unittest.main()