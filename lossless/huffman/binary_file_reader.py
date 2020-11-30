from bitarray import bitarray


class BinaryFileReader:
    """
    This class helps us read a file bit by bit. It internally uses a bitarray to buffer bits from the file. It first
    fills the buffer with 8 bits and return bits from that buffer. It won't fill the buffer up again until it is
    completely consumed.

    The max number of bits stored in the buffer at any given point is 8.
    """

    def __init__(self, file):
        # Always start at the beginning of the file
        file.seek(0)
        self._file_handler = file
        # Fill bitarray buffer with first byte from file
        self._end_of_file = False
        self._buffer = bitarray()
        self._read_bytes_from_file(self._buffer, 1)

    def read_bits(self, number):
        """
        This method reads N bits from a file and returns them in a bitarray. If the file is already finished,
        the returned bitarray will be emtpy.

        :param number: The number of bits to read from the file
        :return: Bitarray containing the required bits from the file
        """
        bits = bitarray()

        if self._end_of_file:
            return bits

        # If reading fewer bits that those available, move buffer but don't refill
        if len(self._buffer) > number:
            bits.extend(self._buffer[:number])
            self._buffer = self._buffer[number:]
        # If reading more bits than those available, keep reading them from file byte by byte and filling
        # up bitarray to return
        else:
            bits.extend(self._buffer)
            number_missing_bits = number - len(self._buffer)
            number_whole_missing_bytes = number_missing_bits // 8

            if number_whole_missing_bytes > 0:
                self._read_bytes_from_file(bits, number_whole_missing_bytes)

            number_final_bits = number_missing_bits % 8

            if number_final_bits > 0:
                temp_bits = bitarray()
                self._read_bytes_from_file(temp_bits, 1)
                bits.extend(temp_bits[:number_final_bits])
                self._buffer = temp_bits[number_final_bits:]
            else:
                self._buffer.clear()
                self._read_bytes_from_file(self._buffer, 1)

        return bits

    def _read_bytes_from_file(self, bits, number):
        try:
            bits.fromfile(self._file_handler, number)
        except EOFError:
            self._end_of_file = True

    def __iter__(self):
        return self

    def __next__(self):
        if self._end_of_file:
            raise StopIteration
        else:
            return self.read_bits(1)
