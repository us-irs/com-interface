import socket
import threading
import time
from collections import deque
from typing import Optional
from unittest import TestCase

from spacepackets import PacketType
from spacepackets.ccsds import PacketId
from spacepackets.ecss import PusTelecommand, PusTelemetry

from com_interface.ip_utils import EthAddr
from com_interface.tcp import TcpSpacepacketsClient

LOCALHOST = "127.0.0.1"


class TestTcpIf(TestCase):
    def setUp(self) -> None:
        self.tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Let the OS assign a port.
        self.addr = (LOCALHOST, 0)
        self.tcp_server.bind(self.addr)
        # Update the address for the client.
        self.addr = self.addr[0], self.tcp_server.getsockname()[1]
        self.tcp_server.listen()
        self.expected_packet_id = PacketId(apid=0x22, sec_header_flag=True, ptype=PacketType.TM)
        self.base_data = bytes([0, 1, 2, 3])
        self.ping_cmd = PusTelecommand(service=17, subservice=1, apid=0x22)
        self.ping_reply = PusTelemetry(service=17, subservice=2, apid=0x22, timestamp=b"")
        self.reply_with_other_packet_id = PusTelemetry(
            service=17, subservice=2, apid=0x40, timestamp=b""
        )
        self.tcp_client = TcpSpacepacketsClient(
            "tcp",
            space_packet_ids=[self.expected_packet_id],
            target_address=EthAddr.from_tuple(self.addr),
            inner_thread_delay=0.05,
        )
        self.conn_socket: Optional[socket.socket] = None
        self.server_received_packets = deque()
        self.tcp_client.initialize()

    def test_monolithic(self):
        self._open()
        tcp_server = threading.Thread(target=self.tcp_echo_server_thread, daemon=True)
        tcp_server.start()
        self._test_basic()
        self._test_send()
        self._test_recv()
        self._test_recv_with_invalid_packet()
        self._test_close_client()

    def tcp_echo_server_thread(self):
        (conn_sock, addr_info) = self.tcp_server.accept()
        while True:
            (data_recv, sender_addr) = conn_sock.recvfrom(4096)
            if len(data_recv) == 0:
                conn_sock.shutdown(socket.SHUT_RDWR)
                conn_sock.close()
                break
            self.server_received_packets.appendleft(data_recv)
            conn_sock.sendall(data_recv)

    def _test_basic(self):
        self.assertEqual(self.tcp_client.id, "tcp")

    def _test_send(self):
        self.tcp_client.send(self.base_data)
        time.sleep(0.2)
        self.assertEqual(len(self.server_received_packets), 1)
        packet = self.server_received_packets.pop()
        self.assertEqual(packet, self.base_data)
        self.server_received_packets.clear()

    def _test_close_client(self):
        self.tcp_client.close()

    def _test_recv(self):
        self.tcp_client.send(self.ping_reply.pack())
        time.sleep(0.2)
        # Assert it arrived at the server
        self.assertEqual(len(self.server_received_packets), 1)
        packet = self.server_received_packets.pop()
        self.assertEqual(packet, self.ping_reply.pack())
        # Now assert that a ping reply was sent back to the client if a ping command was sent
        self.assertEqual(self.tcp_client.packets_available(), 1)
        recvd_packets = self.tcp_client.receive()
        self.assertEqual(len(recvd_packets), 1)
        self.assertEqual(recvd_packets[0], self.ping_reply.pack())
        self.assertEqual(len(self.server_received_packets), 0)
        self.server_received_packets.clear()

    def _test_recv_with_invalid_packet(self):
        self.tcp_client.send(self.ping_cmd.pack())
        self.tcp_client.send(self.ping_reply.pack())
        time.sleep(0.2)
        # Assert both packets arrived at the server
        self.assertEqual(len(self.server_received_packets), 2)
        packet_0 = self.server_received_packets.pop()
        self.assertEqual(packet_0, self.ping_cmd.pack())
        packet_1 = self.server_received_packets.pop()
        self.assertEqual(packet_1, self.ping_reply.pack())

        # Now assert that a ping reply was sent back to the client if a ping command was sent
        self.assertEqual(self.tcp_client.packets_available(), 1)
        recvd_packets = self.tcp_client.receive()
        self.assertEqual(len(recvd_packets), 1)
        self.assertEqual(recvd_packets[0], self.ping_reply.pack())

    def _open(self):
        self.tcp_client.open()
        self.assertTrue(self.tcp_client.is_open())

    def tearDown(self) -> None:
        self.tcp_server.close()
        self.tcp_client.close()
