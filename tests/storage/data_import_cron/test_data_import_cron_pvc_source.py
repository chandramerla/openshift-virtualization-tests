import logging

import pytest

LOGGER = logging.getLogger(__name__)


class TestDataImportCronPvcSource:
    @pytest.mark.polarion("CNV-11842")
    @pytest.mark.s390x
    def test_data_import_cron_with_pvc_source_ready(
        self, namespace, dv_source_for_data_import_cron, data_import_cron_with_pvc_source, imported_data_source
    ):
        imported_data_source.wait_for_condition(
            condition=imported_data_source.Condition.READY, status=imported_data_source.Condition.Status.TRUE
        )

    @pytest.mark.polarion("CNV-11858")
    @pytest.mark.s390x
    def test_data_import_cron_vm_from_import_pvc(self, namespace, vm_for_data_source_import):
        assert vm_for_data_source_import, f"vm {vm_for_data_source_import} did not created from the imported source pvc"
