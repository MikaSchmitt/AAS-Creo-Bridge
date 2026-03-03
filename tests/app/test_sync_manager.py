from __future__ import annotations
import unittest
from unittest.mock import MagicMock, patch

# From the requirements:
# - link AAS items to Creo models
# - synchronization manager keeps track of synchronized files
# - synchronization has two steps: link, then sync contents
# - focus on creating a Creo model from AAS first (extraction)

class TestSynchronizationManager(unittest.TestCase):
    def test_link_aas_to_creo(self) -> None:
        """
        Tests that an AAS shell can be linked to a Creo model.
        """
        from aas_creo_bridge.app.sync_manager import SynchronizationManager, ConnectionLink
        
        manager = SynchronizationManager()
        aas_shell_id = "aas_123"
        creo_model_name = "part_abc"
        
        manager.link(aas_shell_id, creo_model_name)
        
        links = manager.list_links()
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0].aas_shell_id, aas_shell_id)
        self.assertEqual(links[0].creo_model_name, creo_model_name)

    def test_sync_aas_to_creo_extracts_and_creates_model_and_links(self) -> None:
        """
        Syncing AAS->Creo should:
        - extract a model definition from the AAS shell
        - create the model in Creo
        - store/update the link in the manager
        """
        from aas_creo_bridge.app.sync_manager import CreoModelDefinition, SynchronizationManager

        manager = SynchronizationManager()

        extractor = MagicMock()
        creo_adapter = MagicMock()
        manager.set_extractor(extractor)
        manager.set_creo_adapter(creo_adapter)

        aas_shell_id = "aas_123"
        extracted = CreoModelDefinition(source_aas_shell_id=aas_shell_id, model_name="created_from_aas")
        extractor.extract_model.return_value = extracted

        manager.sync_aas_to_creo(aas_shell_id)

        extractor.extract_model.assert_called_once_with(aas_shell_id)
        creo_adapter.create_model.assert_called_once_with(extracted)

        links = manager.list_links()
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0].aas_shell_id, aas_shell_id)
        self.assertEqual(links[0].creo_model_name, "created_from_aas")

    def test_link_overwrites_existing_link_for_same_shell(self) -> None:
        from aas_creo_bridge.app.sync_manager import SynchronizationManager

        manager = SynchronizationManager()
        manager.link("aas_1", "old_model")
        manager.link("aas_1", "new_model")

        links = manager.list_links()
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0].aas_shell_id, "aas_1")
        self.assertEqual(links[0].creo_model_name, "new_model")

    @patch("aas_creo_bridge.app.sync_manager.import_model_into_creo")
    @patch("aas_creo_bridge.app.sync_manager.get_models_from_aas")
    @patch("aas_creo_bridge.app.sync_manager.get_aasx_registry")
    def test_sync_aas_to_creo_fallback_path_uses_registry_and_adapters(
        self,
        registry_factory: MagicMock,
        get_models_from_aas_mock: MagicMock,
        import_model_into_creo_mock: MagicMock,
    ) -> None:
        from aas_creo_bridge.app.sync_manager import SynchronizationManager

        manager = SynchronizationManager()
        registry = MagicMock()
        aasx_obj = object()
        registry.get.return_value = aasx_obj
        registry_factory.return_value = registry
        get_models_from_aas_mock.return_value = []

        manager.sync_aas_to_creo("aas_456")

        registry.get.assert_called_once_with("aas_456")
        get_models_from_aas_mock.assert_called_once_with(aasx_obj, "aas_456")
        # TODO: import_model_into_creo_mock.assert_called_once_with()
