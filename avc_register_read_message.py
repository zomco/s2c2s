"""Avc Register Reading Request/Response."""

__all__ = [
    "AvcReadHoldingRegistersRequest",
    "AvcReadHoldingRegistersResponse",
    "AvcReadRegistersResponseBase",
]

# pylint: disable=missing-type-doc
import struct

from pymodbus.pdu import ExceptionResponse, ModbusRequest, ModbusResponse
from pymodbus.pdu import ModbusExceptions as merror


class AvcReadRegistersRequestBase(ModbusRequest):
    """Base class for reading a modbus register."""

    _rtu_frame_size = 8

    def __init__(self, address, count, slave=0, **kwargs):
        """Initialize a new instance.

        :param address: The address to start the read from
        :param count: The number of registers to read
        :param slave: Modbus slave slave ID
        """
        super().__init__(slave, **kwargs)
        self.address = address
        self.count = count

    def encode(self):
        """Encode the request packet.

        :return: The encoded packet
        """
        return struct.pack(">HH", self.address, self.count)

    def decode(self, data):
        """Decode a register request packet.

        :param data: The request to decode
        """
        self.address, self.count = struct.unpack(">HH", data)

    def get_response_pdu_size(self):
        """Get response pdu size.

        Func_code (1 byte) + Byte Count(1 byte) + 2 * Quantity of Coils (n Bytes).
        """
        return 1 + 1 + 2 * self.count

    def __str__(self):
        """Return a string representation of the instance.

        :returns: A string representation of the instance
        """
        return f"{self.__class__.__name__} ({self.address},{self.count})"


class AvcReadRegistersResponseBase(ModbusResponse):
    """Base class for responding to a modbus register read.

    The requested registers can be found in the .registers list.
    """

    _rtu_byte_count_pos = 2

    def __init__(self, values, slave=0, **kwargs):
        """Initialize a new instance.

        :param values: The values to write to
        :param slave: Modbus slave slave ID
        """
        super().__init__(slave, **kwargs)

        #: A list of register values
        self.registers = values or []

    def encode(self):
        """Encode the response packet.

        :returns: The encoded packet
        """
        result = struct.pack(">B", len(self.registers) * 2)
        for register in self.registers:
            result += struct.pack(">H", register)
        return result

    def decode(self, data):
        """Decode a register response packet.

        :param data: The request to decode
        """
        byte_count = int(data[0])
        self.registers = []
        for i in range(1, byte_count + 1, 2):
            self.registers.append(struct.unpack(">H", data[i : i + 2])[0])

    def getRegister(self, index):
        """Get the requested register.

        :param index: The indexed register to retrieve
        :returns: The request register
        """
        return self.registers[index]

    def __str__(self):
        """Return a string representation of the instance.

        :returns: A string representation of the instance
        """
        return f"{self.__class__.__name__} ({len(self.registers)})"


class AvcReadHoldingRegistersRequest(AvcReadRegistersRequestBase):
    """Read holding registers.

    This function code is used to read the contents of a contiguous block
    of holding registers in a remote device. The Request PDU specifies the
    starting register address and the number of registers. In the PDU
    Registers are addressed starting at zero. Therefore registers numbered
    1-16 are addressed as 0-15.
    """

    function_code = 3
    function_code_name = "read_holding_registers"

    def __init__(self, address=None, count=None, slave=0, **kwargs):
        """Initialize a new instance of the request.

        :param address: The starting address to read from
        :param count: The number of registers to read from address
        :param slave: Modbus slave slave ID
        """
        super().__init__(address, count, slave, **kwargs)

    def execute(self, context):
        """Run a read holding request against a datastore.

        :param context: The datastore to request from
        :returns: An initialized :py:class:`~pymodbus.register_read_message.ReadHoldingRegistersResponse`, or an :py:class:`~pymodbus.pdu.ExceptionResponse` if an error occurred
        """
        if not (1 <= self.count <= 0x7D):
            return self.doException(merror.IllegalValue)
        if not context.validate(self.function_code, self.address, self.count):
            return self.doException(merror.IllegalAddress)
        values = context.getValues(self.function_code, self.address, self.count)
        if isinstance(values, ExceptionResponse):
            return values

        return ReadHoldingRegistersResponse(values)


class AvcReadHoldingRegistersResponse(AvcReadRegistersResponseBase):
    """Read holding registers.

    This function code is used to read the contents of a contiguous block
    of holding registers in a remote device. The Request PDU specifies the
    starting register address and the number of registers. In the PDU
    Registers are addressed starting at zero. Therefore registers numbered
    1-16 are addressed as 0-15.

    The requested registers can be found in the .registers list.
    """

    function_code = 3

    def __init__(self, values=None, **kwargs):
        """Initialize a new response instance.

        :param values: The resulting register values
        """
        super().__init__(values, **kwargs)

