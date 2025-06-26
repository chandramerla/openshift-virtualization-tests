"""
Connectivity over bond bridge on secondary interface
"""

from collections import OrderedDict

import pytest

import utilities.network
from tests.network.libs import cloudinit as netcloud
from utilities.infra import get_node_selector_dict
from utilities.network import (
    BondNodeNetworkConfigurationPolicy,
    assert_ping_successful,
    cloud_init_network_data,
    get_vmi_ip_v4_by_name,
    network_nad,
)
from utilities.virt import VirtualMachineForTests, fedora_vm_body

pytestmark = pytest.mark.usefixtures(
    "hyperconverged_ovs_annotations_enabled_scope_session",
    "workers_type",
)


@pytest.fixture(scope="class")
def ovs_linux_br1bond_nad(bridge_device_matrix__class__, namespace):
    with network_nad(
        namespace=namespace,
        nad_type=bridge_device_matrix__class__,
        nad_name="br1bond-nad",
        interface_name="br1bond",
    ) as nad:
        yield nad


@pytest.fixture(scope="class")
def ovs_linux_bond1_worker_1(
    index_number,
    worker_node1,
    nodes_available_nics,
):
    """
    Create BOND if setup support BOND
    """
    bond_idx = next(index_number)
    with BondNodeNetworkConfigurationPolicy(
        name=f"bond{bond_idx}nncp-worker-1",
        bond_name=f"bond{bond_idx}",
        bond_ports=nodes_available_nics[worker_node1.name][-2:],
        node_selector=get_node_selector_dict(node_selector=worker_node1.hostname),
    ) as bond:
        yield bond


@pytest.fixture(scope="class")
def ovs_linux_bond1_worker_2(
    index_number,
    worker_node2,
    nodes_available_nics,
    ovs_linux_bond1_worker_1,
):
    """
    Create BOND if setup support BOND
    """
    bond_idx = next(index_number)
    with (
        BondNodeNetworkConfigurationPolicy(
            name=f"bond{bond_idx}nncp-worker-2",
            bond_name=ovs_linux_bond1_worker_1.bond_name,  # Use the same BOND name for each test.
            bond_ports=nodes_available_nics[worker_node2.name][-2:],
            node_selector=get_node_selector_dict(node_selector=worker_node2.hostname),
        ) as bond
    ):
        yield bond


@pytest.fixture(scope="class")
def ovs_linux_bridge_on_bond_worker_1(
    bridge_device_matrix__class__,
    worker_node1,
    ovs_linux_br1bond_nad,
    ovs_linux_bond1_worker_1,
):
    """
    Create bridge and attach the BOND to it
    """
    with utilities.network.network_device(
        interface_type=bridge_device_matrix__class__,
        nncp_name="bridge-on-bond-worker-1",
        interface_name=ovs_linux_br1bond_nad.bridge_name,
        node_selector=get_node_selector_dict(node_selector=worker_node1.hostname),
        ports=[ovs_linux_bond1_worker_1.bond_name],
    ) as br:
        yield br


@pytest.fixture(scope="class")
def ovs_linux_bridge_on_bond_worker_2(
    bridge_device_matrix__class__,
    worker_node2,
    ovs_linux_br1bond_nad,
    ovs_linux_bond1_worker_2,
):
    """
    Create bridge and attach the BOND to it
    """
    with utilities.network.network_device(
        interface_type=bridge_device_matrix__class__,
        nncp_name="bridge-on-bond-worker-2",
        interface_name=ovs_linux_br1bond_nad.bridge_name,
        node_selector=get_node_selector_dict(node_selector=worker_node2.hostname),
        ports=[ovs_linux_bond1_worker_2.bond_name],
    ) as br:
        yield br


@pytest.fixture(scope="class")
def ovs_linux_bond_bridge_attached_vma(
    worker_node1,
    namespace,
    unprivileged_client,
    ovs_linux_br1bond_nad,
    ovs_linux_bridge_on_bond_worker_1,
):
    name = "bond-vma"
    networks = OrderedDict()
    networks[ovs_linux_br1bond_nad.name] = ovs_linux_br1bond_nad.name
    netdata = netcloud.NetworkData(ethernets={"eth1": netcloud.EthernetDevice(addresses=["10.200.3.1/24"])})

    with VirtualMachineForTests(
        namespace=namespace.name,
        name=name,
        body=fedora_vm_body(name=name),
        networks=networks,
        interfaces=networks.keys(),
        node_selector=get_node_selector_dict(node_selector=worker_node1.hostname),
        cloud_init_data=netcloud.cloudinit(netdata=netdata),
        client=unprivileged_client,
    ) as vm:
        vm.start()
        yield vm


@pytest.fixture(scope="class")
def ovs_linux_bond_bridge_attached_vmb(
    worker_node2,
    namespace,
    unprivileged_client,
    ovs_linux_br1bond_nad,
    ovs_linux_bridge_on_bond_worker_2,
):
    name = "bond-vmb"
    networks = OrderedDict()
    networks[ovs_linux_br1bond_nad.name] = ovs_linux_br1bond_nad.name
    network_data_data = {"ethernets": {"eth1": {"addresses": ["10.200.3.2/24"]}}}
    cloud_init_data = cloud_init_network_data(data=network_data_data)

    with VirtualMachineForTests(
        namespace=namespace.name,
        name=name,
        body=fedora_vm_body(name=name),
        networks=networks,
        interfaces=networks.keys(),
        node_selector=get_node_selector_dict(node_selector=worker_node2.hostname),
        cloud_init_data=cloud_init_data,
        client=unprivileged_client,
    ) as vm:
        vm.start()
        yield vm


@pytest.fixture(scope="class")
def ovs_linux_bond_bridge_attached_vms(ovs_linux_bond_bridge_attached_vma, ovs_linux_bond_bridge_attached_vmb):
    vms = (ovs_linux_bond_bridge_attached_vma, ovs_linux_bond_bridge_attached_vmb)
    for vm in vms:
        vm.wait_for_ready_status(status=True)
        vm.wait_for_agent_connected()
    yield vms


class TestBondConnectivity:
    @pytest.mark.ipv4
    @pytest.mark.polarion("CNV-3366")
    @pytest.mark.s390x
    def test_bond(
        self,
        namespace,
        ovs_linux_br1bond_nad,
        ovs_linux_bridge_on_bond_worker_1,
        ovs_linux_bridge_on_bond_worker_2,
        ovs_linux_bond_bridge_attached_vms,
    ):
        src_vm, dst_vm = ovs_linux_bond_bridge_attached_vms
        assert_ping_successful(
            src_vm=src_vm,
            dst_ip=get_vmi_ip_v4_by_name(
                vm=dst_vm,
                name=ovs_linux_br1bond_nad.name,
            ),
        )
