import heapq
from bitarray import bitarray


def build_huffman_map(symbol_occurrences):
    """
    This function builds a Huffman map based on the frequencies of the different input symbols. Since this is
    an entropy encoding technique, more frequent symbols are coded with fewer bits.

    It assigns a prefix-free code to each symbol, meaning that it requires that there is no whole code word that
    is a prefix of any other code word. To build this tree:

    - Create a leaf node for each symbol and add it to the priority queue.
    - While there is more than one node in the queue:
        * Remove the two nodes of highest priority (lowest probability) from the queue
        * Create a new internal node with these two nodes as children and with probability equal to the sum of the two nodes' probabilities.
        * Add the new node to the queue.
    - The remaining node is the root node and the tree is complete.


    For more info: https://en.wikipedia.org/wiki/Huffman_coding

    :param symbol_occurrences: Map of symbols to frequencies that we want to find Huffman codes for
    :return: Map of symbols to Huffman codes
    """
    initial_huffman_nodes = \
        [HuffmanTreeNode(symbol, occurrences) for symbol, occurrences in symbol_occurrences.items()]

    huffman_tree_root = _build_huffman_tree(initial_huffman_nodes)

    encoding_map = {}
    _build_huffman_map(huffman_tree_root, encoding_map)
    return encoding_map


# Traverse binary Huffman tree appending 0 when we go left and 1 when we go right to the current huffman
# code constructed. Once we get to a leaf, the construction of the current code is done and we can add it to
# the Huffman map.
def _build_huffman_map(huffman_tree_root, encoding_map, bits=""):
    if not huffman_tree_root.zero_child and not huffman_tree_root.one_child:
        encoding_map[huffman_tree_root.input_symbol] = bitarray(bits)
    else:
        _build_huffman_map(huffman_tree_root.zero_child, encoding_map, bits + "0")
        _build_huffman_map(huffman_tree_root.one_child, encoding_map, bits + "1")


def _build_huffman_tree(huffman_tree_nodes):
    heapq.heapify(huffman_tree_nodes)

    while len(huffman_tree_nodes) > 1:
        # Remove the two nodes with lowest frequency from the priority queue and combine them into a single node
        min_1 = heapq.heappop(huffman_tree_nodes)
        min_2 = heapq.heappop(huffman_tree_nodes)

        # The combined priority queue node contains an internal tree with:
        #   - Root: Te combined symbol and frequency from the two extracted nodes
        #   - Children: Each of the nodes with lowest frequency that we extracted
        combined_node = HuffmanTreeNode(
            "{}{}".format(min_1.input_symbol, min_2.input_symbol),
            min_1.symbol_weight + min_2.symbol_weight,
            zero_child=min_1,
            one_child=min_2
        )

        # Add the new combined node to the priority queue
        heapq.heappush(huffman_tree_nodes, combined_node)

    # At the end, there is a single node in the priority queue containing the whole Huffman tree inside
    return huffman_tree_nodes[0]


class HuffmanTreeNode:
    def __init__(self, input_symbol, symbol_weight, zero_child=None, one_child=None):
        self._input_symbol = input_symbol
        self._symbol_weight = symbol_weight
        self._zero_child = zero_child
        self._one_child = one_child

    @property
    def input_symbol(self):
        return self._input_symbol

    @property
    def symbol_weight(self):
        return self._symbol_weight

    @property
    def zero_child(self):
        return self._zero_child

    @property
    def one_child(self):
        return self._one_child

    @zero_child.setter
    def zero_child(self, node):
        self._zero_child = node

    @one_child.setter
    def one_child(self, node):
        self._one_child = node

    def __lt__(self, other):
        return self._symbol_weight < other.symbol_weight

    def __str__(self):
        return "{}:{}:{}:{}".format(
            self._input_symbol,
            self._symbol_weight,
            self._zero_child.input_symbol if self._zero_child else "None",
            self._one_child.input_symbol if self._one_child else "None"
        )