from __future__ import annotations

import collections
import logging
import threading
import time
from typing import Any

from cobs import cobs

from com_interface import ComInterface
from com_interface.serial_base import SerialCfg, SerialComBase, SerialCommunicationType


class SerialCobsComIF(SerialComBase, ComInterface):
    """Serial communication interface which uses the
    `COBS protocol <https://pypi.org/project/cobs/>`_ to encode and decode packets.

    This class will spin up a receiver thread on the :meth:`open` call to poll
    for COBS encoded packets. It decodes all received COBS frames using :py:func:`cobs.cobs.decode`.
    This means that the :meth:`close` call might block until the receiver thread has shut down.
    """

    def __init__(self, ser_cfg: SerialCfg):
        super().__init__(
            logging.getLogger(__name__),
            ser_cfg=ser_cfg,
            ser_com_type=SerialCommunicationType.COBS,
        )
        self.__polling_shutdown = threading.Event()
        self.__reception_thread: threading.Thread | None = None
        self._packet_deque = collections.deque()
        self._serial_ring_buf = collections.deque()
        self._parse_buffer = bytearray()
        self.parsing_error_count = 0

    def encode_data(self, data: bytes | bytearray) -> bytearray:
        """Encodes the data using the COBS protocol.
        :param data: Data to encode.
        :return: Encoded data.
        """
        encoded = bytearray([0])
        encoded.extend(cobs.encode(data))
        encoded.append(0)
        return encoded

    @property
    def id(self) -> str:
        return self.ser_cfg.com_if_id

    def initialize(self, args: Any = None) -> None:
        pass

    def open(self, args: Any = None) -> None:
        """Spins up a receiver thread to permanently check for new COBS encoded packets."""
        super().open_port()
        self.__polling_shutdown.clear()
        self.__reception_thread = threading.Thread(target=self._poll_cobs_packets, daemon=True)
        self.__reception_thread.start()

    def is_open(self) -> bool:
        return self.serial is not None

    def close(self, args: Any = None) -> None:
        if self.__reception_thread is None:
            return
        self.__polling_shutdown.set()
        self.__reception_thread.join(0.4)
        super().close_port()

    def send(self, data: bytes | bytearray) -> None:
        """This function encodes all data using the :py:func:`cobs.cobs.encode` function."""
        assert self.serial is not None
        self.serial.write(self.encode_data(data))

    def receive(self, parameters: Any = 0) -> list[bytes]:
        packet_list = []
        self._parse_for_packets()
        while self._packet_deque:
            packet_list.append(self._packet_deque.pop())
        return packet_list

    def packets_available(self, parameters: Any = 0) -> int:
        self._parse_for_packets()
        return self._packet_deque.__len__()

    def clear(self) -> None:
        self._packet_deque.clear()
        self._parse_buffer = bytearray()
        self._serial_ring_buf.clear()

    def _parse_for_packets(self) -> None:
        available_fragments = self._serial_ring_buf.__len__()
        while available_fragments > 0:
            self._parse_buffer.extend(self._serial_ring_buf.pop())
            available_fragments -= 1
        self._parsing_algorithm()

    def _parsing_algorithm(self) -> None:
        start_found = False
        start_idx = 0
        for idx, byte in enumerate(self._parse_buffer):
            if byte == 0:
                if start_found:
                    try:
                        packet = cobs.decode(self._parse_buffer[start_idx + 1 : idx])
                        if len(packet) > 0:
                            self._packet_deque.appendleft(packet)
                    except cobs.DecodeError:
                        self.parsing_error_count += 1
                    self._parse_buffer = self._parse_buffer[idx + 1 :]
                    if len(self._parse_buffer) > 0:
                        self._parsing_algorithm()
                else:
                    start_found = True
                    start_idx = idx

    def _poll_cobs_packets(self) -> None:
        assert self.serial is not None
        # Poll permanently, but it is possible to join this thread every 200 ms
        # Timeout of 0, we poll and delay ourselves.
        self.serial.timeout = 0
        while True:
            bytes_received = self.serial.read()
            self._serial_ring_buf.appendleft(bytes_received)
            if len(bytes_received) == 0:
                time.sleep(self.ser_cfg.polling_frequency)
            if self.__polling_shutdown.is_set():
                break
