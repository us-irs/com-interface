"""UDP Communication Interface"""

from __future__ import annotations

import logging
import select
import socket
from typing import TYPE_CHECKING, Any

from com_interface import ComInterface

if TYPE_CHECKING:
    from com_interface.ip_utils import EthAddr

_LOGGER = logging.getLogger(__name__)


class UdpClient(ComInterface):
    """Communication interface for UDP communication"""

    def __init__(
        self,
        com_if_id: str,
        send_address: EthAddr,
        recv_addr: None | EthAddr = None,
    ):
        """Initialize a communication interface to send and receive UDP datagrams.

        :param send_address:
        :param recv_addr:
        """
        self.udp_socket = None
        self.com_if_id = com_if_id
        self.send_address = send_address
        self.recv_addr = recv_addr

    @property
    def id(self) -> str:
        return self.com_if_id

    def __del__(self):
        try:
            self.close()
        except OSError:
            _LOGGER.warning("Could not close UDP communication interface")

    def initialize(self, args: Any = None) -> Any:
        pass

    def open(self, args: Any = None) -> None:
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Bind is possible but should not be necessary, and introduces risk of port already
        # being used.
        # See: https://docs.microsoft.com/en-us/windows/win32/api/winsock/nf-winsock-bind
        if self.recv_addr is not None:
            _LOGGER.info(
                f"Binding UDP socket to {self.recv_addr.ip_addr} and port {self.recv_addr.port}"
            )
            self.udp_socket.bind(self.recv_addr.to_tuple)
        # Set non-blocking because we use select
        self.udp_socket.setblocking(False)

    def is_open(self) -> bool:
        return self.udp_socket is not None

    def close(self, args: any | None = None) -> None:
        if self.udp_socket is not None:
            self.udp_socket.close()

    def send(self, data: bytes | bytearray) -> None:
        if self.udp_socket is None:
            return
        bytes_sent = self.udp_socket.sendto(data, self.send_address.to_tuple)
        if bytes_sent != len(data):
            _LOGGER.warning("Not all bytes were sent!")

    def packets_available(self, parameters: Any = 0) -> bool:
        if self.udp_socket is None:
            return False
        ready = select.select([self.udp_socket], [], [], 0)
        return bool(ready[0])

    def receive(self, parameter: Any = 0) -> list[bytes]:
        packet_list = []
        if self.udp_socket is None:
            return packet_list
        try:
            while self.packets_available() > 0:
                data, sender_addr = self.udp_socket.recvfrom(4096)
                packet_list.append(bytearray(data))
            return packet_list
        except ConnectionResetError:
            _LOGGER.warning("Connection reset exception occured!")
            return []
