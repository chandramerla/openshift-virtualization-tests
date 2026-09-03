# global_config_multiarch_s390x_arm.py
#
# Multi-arch config for s390x + arm64 heterogeneous clusters with ODF/Ceph storage.
# Topology: s390x control plane + s390x workers + arm64 worker(s).
# Storage:  ocs-storagecluster-ceph-rbd-virtualization (RWX Block, snapshot-capable).
#
# Follows the same pattern as:
#   global_config_multiarch.py    — amd64+arm64 hetero on AWS (IO2 storage)
#   global_config_rh_it.py        — RH internal NFS
#
# Usage (per-arch split, mirrors RH's infra/storage/virt pattern):
#   pytest tests/infrastructure \
#     --tc-file=tests/global_config_multiarch_s390x_arm.py --tc-format=python \
#     --cpu-arch=s390x -m "tier2 and infrastructure and not special_infra and s390x"
#
#   pytest tests/infrastructure \
#     --tc-file=tests/global_config_multiarch_s390x_arm.py --tc-format=python \
#     --cpu-arch=arm64 -m "tier2 and infrastructure and not special_infra and arm64"
#
# Usage (combined, mirrors RH's network/IUO pattern):
#   pytest tests/network \
#     --tc-file=tests/global_config_multiarch_s390x_arm.py --tc-format=python \
#     --cpu-arch=s390x,arm64 -m "network and multiarch and single_nic"
#
# Pre-requisites (upstream PRs):
#   1. SUPPORTED_MULTIARCH_OPTIONS must include S390X (utilities/constants/architecture.py)
#   2. global_config_multiarch.py os_matrix must have S390X entry

from typing import Any

import pytest_testconfig
from ocp_resources.datavolume import DataVolume

from utilities.constants.architecture import (
    ARM_64,
    S390X,
)
from utilities.constants.images import OS_FLAVOR_FEDORA
from utilities.constants.instance_types import (
    CENTOS_STREAM9_PREFERENCE,
    RHEL9_PREFERENCE,
    RHEL10_PREFERENCE,
    U1_MEDIUM_STR,
)
from utilities.constants.storage import StorageClassNames

global config
global_config = pytest_testconfig.load_python(py_file="tests/global_config.py", encoding="utf-8")

# ODF Ceph RBD Virtualization — correct SC for s390x+arm64 clusters using ODF
# (global_config_multiarch.py uses AWS IO2_CSI, not applicable here)
storage_class_matrix = [
    {
        StorageClassNames.CEPH_RBD_VIRTUALIZATION: {
            "volume_mode": DataVolume.VolumeMode.BLOCK,
            "access_mode": DataVolume.AccessMode.RWX,
            "snapshot": True,
            "online_resize": True,
            "wffc": False,  # ODF does not require WaitForFirstConsumer
            "default": True,
        }
    },
]

storage_class_a = StorageClassNames.CEPH_RBD_VIRTUALIZATION
storage_class_b = StorageClassNames.CEPH_RBD_VIRTUALIZATION

os_matrix = {
    S390X: {
        "rhel_os_list": ["rhel-9-6"],
        "fedora_os_list": ["fedora-42"],
        "centos_os_list": ["centos-stream-9"],
        "instance_type_rhel_os_list": [RHEL9_PREFERENCE],
        "instance_type_fedora_os_list": [OS_FLAVOR_FEDORA],
        "instance_type_centos_os_list": [CENTOS_STREAM9_PREFERENCE],
        "data_import_cron_matrix": [
            {"centos-stream9-s390x": {"instance_type": U1_MEDIUM_STR, "preference": CENTOS_STREAM9_PREFERENCE}},
            {"fedora-s390x": {"instance_type": U1_MEDIUM_STR, "preference": OS_FLAVOR_FEDORA}},
            {"rhel9-s390x": {"instance_type": U1_MEDIUM_STR, "preference": RHEL9_PREFERENCE}},
        ],
        "auto_update_data_source_matrix": [
            {"centos-stream9-s390x": {"template_os": "centos-stream9"}},
            {"fedora-s390x": {"template_os": "fedora"}},
            {"rhel9-s390x": {"template_os": "rhel9.0"}},
        ],
    },
    ARM_64: {
        "rhel_os_list": ["rhel-9-6"],
        "fedora_os_list": ["fedora-42"],
        "centos_os_list": ["centos-stream-9"],
        "instance_type_rhel_os_list": [RHEL10_PREFERENCE],
        "instance_type_fedora_os_list": [OS_FLAVOR_FEDORA],
        "data_import_cron_matrix": [
            {"centos-stream9-arm64": {"instance_type": U1_MEDIUM_STR, "preference": CENTOS_STREAM9_PREFERENCE}},
            {"fedora-arm64": {"instance_type": U1_MEDIUM_STR, "preference": f"{OS_FLAVOR_FEDORA}.{ARM_64}"}},
            {"rhel9-arm64": {"instance_type": U1_MEDIUM_STR, "preference": f"{RHEL9_PREFERENCE}.{ARM_64}"}},
        ],
        "auto_update_data_source_matrix": [
            {"centos-stream9-arm64": {"template_os": "centos-stream9"}},
            {"fedora-arm64": {"template_os": "fedora"}},
            {"rhel9-arm64": {"template_os": "rhel9.0"}},
        ],
    },
}


for _dir in dir():
    if not config:  # noqa: F821
        config: dict[str, Any] = {}
    val = locals()[_dir]
    if type(val) not in [bool, list, dict, str]:
        continue

    if _dir in ["encoding", "py_file"]:
        continue

    config[_dir] = locals()[_dir]  # noqa: F821
