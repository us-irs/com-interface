import os
import sys
import time
import unittest
from unittest import TestCase

from com_interface.serial_base import SerialCfg
from com_interface.serial_cobs import SerialCobsComIF


@unittest.skipIf(sys.platform.startswith("win"), "pty only works on POSIX systems")
class TestSerialCobsInterface(TestCase):
    def setUp(self) -> None:
        import pty

        self._pty_master, slave = pty.openpty()
        sname = os.ttyname(slave)
        ser_cfg = SerialCfg(
            com_if_id="pseudo_ser_cobs",
            serial_port=sname,
            baud_rate=9600,
        )
        self._cobs_if = SerialCobsComIF(ser_cfg)
        self._cobs_if.open()
        self._cobs_if.initialize()

    def test_monolithic(self):
        self._test_state()
        self._cobs_if.clear()
        self._test_send()
        self._cobs_if.clear()
        self._test_recv()
        self._cobs_if.clear()
        self._test_recv_consecutive()

    def _test_state(self):
        self.assertTrue(self._cobs_if.is_open())
        self.assertEqual(self._cobs_if.packets_available(0), 0)
        self.assertEqual(self._cobs_if.id, "pseudo_ser_cobs")

    def _test_send(self):
        from cobs import cobs

        test_data = bytes([0x01, 0x02, 0x03])
        encoded_len = len(cobs.encode(test_data))
        self._cobs_if.send(test_data)
        encoded_packet = os.read(self._pty_master, encoded_len + 2)
        test_data_read_back = cobs.decode(encoded_packet[1:-1])
        self.assertEqual(test_data_read_back, test_data)

    def _test_recv(self):
        from cobs import cobs

        self._cobs_if.clear()

        test_data = bytes([0x02, 0x03, 0x04])
        encoded_test_data = cobs.encode(test_data)
        # Add packer delimiters.
        full_data_to_send = bytearray([0x00])
        full_data_to_send.extend(encoded_test_data)
        full_data_to_send.append(0)
        os.write(self._pty_master, full_data_to_send)
        # Give the receiver thread some time to do its work.
        time.sleep(0.15)
        self.assertEqual(self._cobs_if.packets_available(0), 1)
        packet_list = self._cobs_if.receive()
        self.assertEqual(len(packet_list), 1)
        # Received data should be decoded now
        self.assertEqual(packet_list[0], test_data)

    def _test_recv_consecutive(self):
        from cobs import cobs

        test_data = bytes([0x02, 0x03, 0x04])
        encoded_data = cobs.encode(test_data)
        # Add packer delimiters.
        full_data_to_send = bytearray([0x00])
        full_data_to_send.extend(encoded_data)
        full_data_to_send.append(0)
        full_data_to_send.append(0)
        test_data_2 = bytes([0x04, 0x02, 0x01])
        encoded_data = cobs.encode(test_data_2)
        full_data_to_send.extend(encoded_data)
        full_data_to_send.append(0)
        os.write(self._pty_master, full_data_to_send)
        # Give the receiver thread some time to do its work.
        time.sleep(0.15)
        self.assertEqual(self._cobs_if.packets_available(0), 2)
        packet_list = self._cobs_if.receive()
        self.assertEqual(len(packet_list), 2)
        # Received data should be decoded now
        self.assertEqual(packet_list[0], test_data)
        self.assertEqual(packet_list[1], test_data_2)

    def tearDown(self) -> None:
        self._cobs_if.close()
