from __future__ import annotations

import enum
from dataclasses import dataclass
from enum import auto

DEFAULT_MAX_RECV_SIZE = 1500


@dataclass
class EthAddr:
    ip_addr: str
    port: int

    @property
    def to_tuple(self) -> tuple[str, int]:
        return self.ip_addr, self.port

    @classmethod
    def from_tuple(cls, addr: tuple[str, int]) -> EthAddr:
        return cls(addr[0], addr[1])


class TcpIpType(enum.Enum):
    TCP = enum.auto()
    UDP = enum.auto()
    UDP_RECV = enum.auto()


class TcpIpConfigIds(enum.Enum):
    SEND_ADDRESS = auto()
    RECV_ADDRESS = auto()
    RECV_MAX_SIZE = auto()
    # Used by TCP to detect start of space packets
    SPACE_PACKET_ID = auto()
