"""Communication module. Provides generic abstraction for communication and commonly used
concrete implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ReceptionDecodeError(Exception):
    """Generic decode error which can also wrap the exception thrown by other libraries."""

    def __init__(self, msg: str, custom_exception: None | Exception):
        super().__init__(msg)
        self.custom_exception = custom_exception


class SendError(Exception):
    """Generic send error which can also wrap the exception thrown by other libraries."""

    def __init__(self, msg: str, custom_exception: None | Exception):
        super().__init__(msg)
        self.custom_exception = custom_exception


class ComInterface(ABC):
    """Generic form of a communication interface to separate communication logic from
    the underlying interface.
    """

    @property
    @abstractmethod
    def id(self) -> str:
        pass

    @abstractmethod
    def initialize(self, args: Any = 0) -> Any:
        """Perform initializations step which can not be done in constructor or which require
        returnvalues.
        """

    @abstractmethod
    def open(self, args: Any = 0) -> None:
        """Opens the communication interface to allow communication.

        :return:
        """

    @abstractmethod
    def is_open(self) -> bool:
        """Can be used to check whether the communication interface is open. This is useful if
        opening a COM interface takes a longer time and is non-blocking
        """

    @abstractmethod
    def close(self, args: Any = 0) -> None:
        """Closes the ComIF and releases any held resources (for example a Communication Port).

        :return:
        """

    @abstractmethod
    def send(self, data: bytes | bytearray) -> None:
        """Send raw data.

        :raises SendError: Sending failed for some reason.
        """

    @abstractmethod
    def receive(self, parameters: Any = 0) -> list[bytes]:
        """Returns a list of received packets. The child class can use a separate thread to poll for
        the packets or use some other mechanism and container like a deque to store packets
        to be returned here.

        :param parameters:
        :raises ReceptionDecodeError: If the underlying COM interface uses encoding and
            decoding and the decoding fails, this exception will be returned.
        :return:
        """
        return []

    @abstractmethod
    def packets_available(self, parameters: Any = 0) -> int:
        """Poll whether packets are available.

        :param parameters: Can be an arbitrary parameter.
        :raises ReceptionDecodeError: If the underlying COM interface uses encoding and
            decoding when determining the number of available packets, this exception can be
            thrown on decoding errors.
        :return: Number of packets available.
        """
