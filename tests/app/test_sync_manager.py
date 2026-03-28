from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

import pytest


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
        from aas_creo_bridge.app.context import get_sync_manager

        manager = get_sync_manager()
        manager.unlink_all()
        aas_shell_id = "aas_123"
        creo_model_name = "part_abc"

        manager.link(aas_shell_id, creo_model_name)

        links = manager.list_links()
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0].aas_shell_id, aas_shell_id)
        self.assertEqual(links[0].creo_model_name, creo_model_name)

    def test_link_overwrites_existing_link_for_same_shell(self) -> None:
        from aas_creo_bridge.app.context import get_sync_manager

        manager = get_sync_manager()
        manager.unlink_all()
        manager.link("aas_1", "old_model")
        manager.unlink("aas_1")
        manager.link("aas_1", "new_model")

        links = manager.list_links()
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0].aas_shell_id, "aas_1")
        self.assertEqual(links[0].creo_model_name, "new_model")

    def test_link_supports_lookup_in_both_directions(self) -> None:
        from aas_creo_bridge.app.context import get_sync_manager

        manager = get_sync_manager()
        manager.unlink_all()
        manager.link("aas_1", "model_1")

        self.assertEqual(manager.get_link_by_aas_id("aas_1").creo_model_name, "model_1")
        self.assertEqual(manager.get_link_by_creo_model("model_1").aas_shell_id, "aas_1")

    def test_link_moves_model_when_reassigned_to_other_aas(self) -> None:
        from aas_creo_bridge.app.context import get_sync_manager

        manager = get_sync_manager()
        manager.unlink_all()
        manager.link("aas_1", "shared_model")

        with pytest.raises(RuntimeError, match=f"Creo model shared_model is already linked to a different AAS shell"):
            manager.link("aas_2", "shared_model")

        self.assertEqual(manager.get_link_by_aas_id("aas_1").creo_model_name, "shared_model")

    def test_unlink_clears_forward_and_reverse_lookup(self) -> None:
        from aas_creo_bridge.app.context import get_sync_manager

        manager = get_sync_manager()
        manager.unlink_all()
        manager.link("aas_1", "model_1")

        manager.unlink("aas_1")

        self.assertIsNone(manager.get_link_by_aas_id("aas_1"))
        self.assertIsNone(manager.get_link_by_creo_model("model_1"))

    def test_link_normalizes_creo_model_name_to_lowercase(self) -> None:
        from aas_creo_bridge.app.context import get_sync_manager

        manager = get_sync_manager()
        manager.unlink_all()
        manager.link("aas_1", "Model_ABC.PRT")

        self.assertEqual(manager.get_link_by_aas_id("aas_1").creo_model_name, "model_abc.prt")
        self.assertEqual(manager.get_link_by_creo_model("MODEL_ABC.PRT").aas_shell_id, "aas_1")

    def test_unlink_by_creo_model_is_case_insensitive(self) -> None:
        from aas_creo_bridge.app.context import get_sync_manager

        manager = get_sync_manager()
        manager.unlink_all()
        manager.link("aas_1", "Part_01")

        manager.unlink("PART_01")

        self.assertIsNone(manager.get_link_by_aas_id("aas_1"))
        self.assertIsNone(manager.get_link_by_creo_model("part_01"))

    """
    @patch("aas_creo_bridge.app.sync_manager.materialize_model_file")
    @patch("aas_creo_bridge.app.sync_manager.select_best_model")
    @patch("aas_creo_bridge.app.sync_manager.get_models_from_aas")
    @patch("aas_creo_bridge.app.sync_manager.get_aasx_registry")
    @patch("aas_creo_bridge.app.sync_manager.get_creoson_client")
    @patch("aas_creo_bridge.app.sync_manager.import_model_into_creo")
    def test_sync_aas_to_creo_uses_registry_selection_and_materializer(
            self,
            import_model_into_creo_mock: MagicMock,
            get_creoson_client_mock: MagicMock,
            registry_factory: MagicMock,
            get_models_from_aas_mock: MagicMock,
            select_best_model_mock: MagicMock,
            materialize_model_file_mock: MagicMock,
    ) -> None:
        from aas_creo_bridge.app.context import get_sync_manager

        manager = get_sync_manager()
        manager.unlink_all()
        registry = MagicMock()
        aasx_obj = object()
        models = [MagicMock()]
        best_model = MagicMock()
        prepared = MagicMock()
        prepared.extracted_path = "C:/temp/model.step"
        creoson_client = MagicMock()

        registry.get.return_value = aasx_obj
        registry_factory.return_value = registry
        get_models_from_aas_mock.return_value = models
        select_best_model_mock.return_value = best_model
        materialize_model_file_mock.return_value = prepared
        get_creoson_client_mock.return_value = creoson_client

        manager.sync_aas_to_creo("aas_456")

        registry.get.assert_called_once_with("aas_456")
        get_models_from_aas_mock.assert_called_once_with(aasx_obj, "aas_456")
        select_best_model_mock.assert_called_once_with(
            models,
            manager._application,
            manager._file_format,
        )
        materialize_model_file_mock.assert_called_once_with(
            aasx_obj,
            best_model,
            manager.out_dir,
        )
        get_creoson_client_mock.assert_called_once_with()
        import_model_into_creo_mock.assert_called_once_with(
            creoson_client,
            prepared.extracted_path,
        )
    """

    @patch("aas_creo_bridge.app.sync_manager.materialize_model_file")
    @patch("aas_creo_bridge.app.sync_manager.select_best_model")
    @patch("aas_creo_bridge.app.sync_manager.get_models_from_aas")
    @patch("aas_creo_bridge.app.sync_manager.get_aasx_registry")
    def test_sync_aas_to_creo_does_not_materialize_when_no_model_is_selected(
            self,
            registry_factory: MagicMock,
            get_models_from_aas_mock: MagicMock,
            select_best_model_mock: MagicMock,
            materialize_model_file_mock: MagicMock,
    ) -> None:
        from aas_creo_bridge.app.context import get_sync_manager

        manager = get_sync_manager()
        manager.unlink_all()
        registry = MagicMock()
        aasx_obj = object()

        registry.get.return_value = aasx_obj
        registry_factory.return_value = registry
        get_models_from_aas_mock.return_value = []
        select_best_model_mock.return_value = None

        manager.sync_aas_to_creo("aas_456")

        registry.get.assert_called_once_with("aas_456")
        get_models_from_aas_mock.assert_called_once_with(aasx_obj, "aas_456")
        select_best_model_mock.assert_called_once_with(
            [],
            manager._application,
            manager._file_format,
        )
        materialize_model_file_mock.assert_not_called()
