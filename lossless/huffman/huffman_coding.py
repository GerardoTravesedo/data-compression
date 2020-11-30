import os
from bitarray import bitarray
from lossless.huffman.binary_file_reader import BinaryFileReader
from lossless.huffman.huffman_map import build_huffman_map


def encode(file_path):
    """
    Uses Huffman codes to encode an input file. It finds the Huffman codes based on the content of the file and stores
    them in the encoded file itself.

    The encoded file is created in the same folder where the input file is located. The extension of the file is .huff

    @:param file_path: path to the input file to encode
    """

    output_path = os.path.splitext(file_path)[0] + ".huff"

    encoding_map = build_huffman_map(_get_symbol_occurrences(file_path))

    print("Huffman codes: {}".format(encoding_map))

    encoded_input = bitarray()

    with open(file_path, 'r') as inputf:
        for line in inputf:
            encoded_input.encode(encoding_map, line)

    # Huffman map is added at the beginning of the encoded file to be able to decode it later
    encoded_content = _encode_huffman_map(encoding_map)
    # Adding the encoded input file
    encoded_content.extend(encoded_input)
    # Adding end-of-file
    encoded_content.extend(encoding_map[u"\u001C"])

    with open(output_path, 'wb') as outputf:
        encoded_content.tofile(outputf)


def decode(input_path, output_path):
    """
    Decodes a file with extension .huff using the Huffman codes that can be found at the beginning of the
    encoded file itself.

    The content of a encoded file follows this structure:
        - For each Huffman map entry:
            * 2 bits representing the number of bytes of the symbol in UTF-8
            * The symbol in UTF-8 (from 1 to 4 bytes)
            * 5 bits representing the number of bytes for the Huffman code associated with the symbol
            * The Huffman code for the symbol
        - SEPARATOR 3 (u"\u001D") to separate map and encoded input file
        - Encoded input file using Huffman codes
        - SEPARATOR 4 (u"\u001C") to indicate end-of-file

    @:param file_path: path to the input file to encode
    """

    is_map_decoding_done = False
    decoding_map = {}

    with open(input_path, 'rb') as f:
        reader = BinaryFileReader(f)

        # Keep decoding every Huffman map entry until all entries are covered
        while not is_map_decoding_done:
            is_map_decoding_done = _decode_huffman_map_entry(decoding_map, reader)

        all_encodings = decoding_map.keys()

        with open(output_path, 'w') as outf:
            encoding = bitarray()

            # Reading remaining bits one at a time. It will match these bits to Huffman codes
            for bit in reader:
                encoding.extend(bit)

                if encoding.to01() in all_encodings:
                    symbol = decoding_map[encoding.to01()]

                    # It stops when it reaches the end-of-file SEPARATOR 4
                    if symbol == u"\u001C":
                        break

                    outf.write(symbol)
                    encoding.clear()


# Returns true if we it is done reading the encoding map. This happens when the entry read is unicode SEPARATOR 3
def _decode_huffman_map_entry(decoding_map, reader):
    # Two bits indicating the size in bytes of the UTF-8 symbol
    utf8_symbol_number_bytes = int(reader.read_bits(2).to01(), 2)

    # Reading necessary bytes to decode UTF-8 symbol
    utf8_symbol_binary = reader.read_bits(utf8_symbol_number_bytes * 8)
    utf8_symbol = utf8_symbol_binary.tobytes().decode('utf-8')

    # It symbol is SEPARATOR 3, then it reached the end of the map
    if utf8_symbol == u"\u001D":
        print("Done reading encoding map")
        return True

    # Five bits indicating the number of bits in the Huffman code associated with the symbol
    encoding_number_bits = int(reader.read_bits(5).to01(), 2)

    # Reading Huffman code
    encoding_bits = reader.read_bits(encoding_number_bits)

    print('Decoded map entry {} -> {} with UTF-8 character bits {}'
          .format(encoding_bits.to01(), utf8_symbol, utf8_symbol_binary.to01()))

    decoding_map[encoding_bits.to01()] = utf8_symbol

    return False


def _encode_huffman_map(encoding_map):
    encoded_map = bitarray()

    for (symbol, code) in encoding_map.items():
        encoded_map.extend(_encode_huffman_map_entry(symbol, code))

    # Adding unicode separator 3 at the end to indicate we are done with the map encoding
    encoded_map.extend("01")
    encoded_map.frombytes(bytes(u"\u001D", 'utf-8'))

    print("Encoded map length: {}".format(len(encoded_map)))

    return encoded_map


def _encode_huffman_map_entry(symbol, code):
    symbol_bytes = bytes(symbol, 'utf-8')
    number_bytes_symbol = len(symbol_bytes)

    # The max number of bytes for utf-8 is 4, so we only need 2 bits to encode that
    encoded_entry = bitarray('{0:02b}'.format(number_bytes_symbol))
    encoded_entry.frombytes(symbol_bytes)

    number_bits_code = len(code)
    # Assuming a max of 32 bits per code, so using 5 bits to encode that
    encoded_entry.extend('{0:05b}'.format(number_bits_code))
    encoded_entry.extend(code)

    print("Total encoded entry {} -> {} : {} with {} code bits"
          .format(symbol, code, encoded_entry, number_bits_code))

    return encoded_entry


def _get_symbol_occurrences(file_path):
    total_occurrences = 0
    symbol_occurrences = {}

    with open(file_path, 'r') as f:
        for line in f:
            for symbol in line:
                total_occurrences += 1

                symbol_occurrences[symbol] = \
                    symbol_occurrences[symbol] + 1 if symbol in symbol_occurrences else 1

    # Adding special symbol (unicode separator 4) that will be used to indicate the end of encoded file
    symbol_occurrences[u"\u001C"] = 1

    print("Symbol occurrences: {}. Total number of symbols: {}"
          .format(symbol_occurrences, len(symbol_occurrences)))

    return symbol_occurrences


if __name__ == "__main__":
    encode("../resources/world192.txt")
    # decode("../resources/article.huff", "../resources//article2.txt")
