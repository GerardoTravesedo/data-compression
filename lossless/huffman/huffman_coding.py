import math
import argparse
import lossless.huffman.paths as paths

from bitarray import bitarray
from lossless.huffman.binary_file_reader import BinaryFileReader
from lossless.huffman.huffman_map import build_huffman_map
from lossless.huffman.grouping_file_reader import GroupingFileReader


def encode(file_path, output_path, block_size, bits_utf8_block):
    """
    Uses Huffman codes to encode an input file. It finds the Huffman codes based on the content of the file and stores
    them at the beginning of the encoded file itself.

    The encoded file is created in output_path. The extension of the file is .huff

    @:param file_path: path to the input file to encode
    @:param output_path: path where to put the encoded file with extension .huff
    @:param block_size: number of consecutive symbols to encode together
    @:param bits_utf8_block: number of bits needed to represent each UTF-8 block
    """
    output_path = paths.get_compressed_output_path(file_path, output_path)

    encoding_map = build_huffman_map(_get_symbol_occurrences(file_path, block_size))

    print("Huffman codes: {}".format(encoding_map))

    encoded_input = bitarray()

    with open(file_path, 'r') as inputf:
        grouping_reader = GroupingFileReader(inputf, group_size=block_size)

        for groups in grouping_reader:
            encoded_input.encode(encoding_map, groups)

    # Huffman map is added at the beginning of the encoded file to be able to decode it later
    encoded_content = _encode_huffman_map(encoding_map, bits_utf8_block)
    # Adding the encoded input file
    encoded_content.extend(encoded_input)
    # Adding end-of-file
    encoded_content.extend(encoding_map[u"\u001C"])

    with open(output_path, 'wb') as outputf:
        encoded_content.tofile(outputf)


def decode(input_path, output_path, bits_utf8_block):
    """
    Decodes a file with extension .huff using the Huffman codes that can be found at the beginning of the
    encoded file itself.

    The content of a encoded file follows this structure:
        - For each Huffman map entry:
            * bits_utf8_block bits representing the number of bytes of the symbol (or block of symbols) in UTF-8
            * The symbol (or block) in UTF-8 (from 1 to 4 bytes each)
            * 5 bits representing the number of bytes for the Huffman code associated with the symbol
            * The Huffman code for the symbol
        - SEPARATOR 3 (u"\u001D") to separate map and encoded input file
        - Encoded input file using Huffman codes
        - SEPARATOR 4 (u"\u001C") to indicate end-of-file

    @:param file_path: path to the input file to encode
    @:param output_path: path where to put the encoded file with extension .huff
    @:param bits_utf8_block: number of bits needed to represent each UTF-8 block
    """
    output_path = paths.get_decompressed_output_path(input_path, output_path)

    is_map_decoding_done = False
    decoding_map = {}

    with open(input_path, 'rb') as f:
        reader = BinaryFileReader(f)

        # Keep decoding every Huffman map entry until all entries are covered
        while not is_map_decoding_done:
            is_map_decoding_done = _decode_huffman_map_entry(decoding_map, reader, bits_utf8_block)

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
def _decode_huffman_map_entry(decoding_map, reader, bits_utf8_block):
    utf8_symbol_number_bytes = int(reader.read_bits(bits_utf8_block).to01(), 2)

    # Reading necessary bytes to decode UTF-8 symbol
    utf8_symbol_binary = reader.read_bits(utf8_symbol_number_bytes * 8)
    utf8_symbol = utf8_symbol_binary.tobytes().decode('utf-8')

    # If symbol is SEPARATOR 3, then it reached the end of the map
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


def _encode_huffman_map(encoding_map, bits_utf8_block):
    encoded_map = bitarray()

    for (symbol, code) in encoding_map.items():
        encoded_map.extend(_encode_huffman_map_entry(symbol, code, bits_utf8_block))

    # Adding unicode separator 3 at the end to indicate we are done with the map encoding
    # The separator is represented with 1 byte in UTF-8, so we use a 1 in binary to indicate the size
    encoded_map.extend("0" * (bits_utf8_block - 1) + "1")
    encoded_map.frombytes(bytes(u"\u001D", 'utf-8'))

    print("Encoded map length: {}".format(len(encoded_map)))

    return encoded_map


def _encode_huffman_map_entry(symbol, code, bytes_utf8_block):
    symbol_bytes = bytes(symbol, 'utf-8')
    number_bytes_symbol = len(symbol_bytes)

    # The max number of bytes for utf-8 is 4 and each block contains BLOCK_SIZE chars
    encoded_entry = bitarray('{0:0{num_bits}b}'.format(number_bytes_symbol, num_bits=bytes_utf8_block))
    encoded_entry.frombytes(symbol_bytes)

    number_bits_code = len(code)
    # Assuming a max of 32 bits per code, so using 5 bits to encode that
    encoded_entry.extend('{0:05b}'.format(number_bits_code))
    encoded_entry.extend(code)

    print("Total encoded entry {} -> {} : {} with {} code bits"
          .format(symbol, code, encoded_entry, number_bits_code))

    return encoded_entry


def _get_symbol_occurrences(file_path, block_size):
    symbol_occurrences = {}

    with open(file_path, 'r') as f:
        grouping_reader = GroupingFileReader(f, group_size=block_size)

        for groups in grouping_reader:
            for symbol in groups:
                symbol_occurrences[symbol] = \
                    symbol_occurrences[symbol] + 1 if symbol in symbol_occurrences else 1

    # Adding special symbol (unicode separator 4) that will be used to indicate the end of encoded file
    symbol_occurrences[u"\u001C"] = 1

    print("Symbol occurrences: {}. Total number of symbols: {}"
          .format(symbol_occurrences, len(symbol_occurrences)))

    return symbol_occurrences


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)

    parser.add_argument(
        "-f", "--file",
        help="File to compress / decompress",
        type=str,
        required=True
    )

    group.add_argument(
        "-c", "--compress",
        help="Compress file",
        action="store_true"
    )

    group.add_argument(
        "-d", "--decompress",
        help="Decompress file",
        action="store_true"
    )

    parser.add_argument(
        "-b", "--block-size",
        help="Number of input characters to encode together as a group",
        type=int,
        default=2
    )

    parser.add_argument(
        "-o", "--output",
        help="Path where the compressed / decompressed generated file will be stored. The default value is the path "
             "from which the script was executed",
        default="."
    )

    args = parser.parse_args()

    # The number of bits needed to represent the number of UTF-8 bytes depends on the block size. Also the max number
    # of bytes per UTF-8 character is 4. For example, if our blocks consists of 3 characters, that means we need a max
    # of 3 * 4 = 12 characters to represent a block. The number of bits we need to represent a 12 is ceil(log(12)) = 4.
    bits_utf8_block = math.ceil(math.log(args.block_size * 4, 2))

    if not args.compress and not args.decompress:
        raise ValueError("Either --compress or --decompress needs to be specified")

    if args.compress:
        print("Compressing file {}".format(args.file))
        encode(args.file, args.output, args.block_size, bits_utf8_block)
    elif args.decompress:
        print("Decompressing file {}".format(args.file))
        decode(args.file, args.output, bits_utf8_block)
    else:
        print("Neither compressing not decompressing")
