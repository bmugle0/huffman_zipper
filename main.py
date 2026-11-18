import json, sys, struct
from CommandTree import RootNode, FunctionNode, LiteralNode, CaptureNode, ParseContext
from Counter import Counter

class MinHeapNode:
    def __init__(self, value, frequency, children = None):
        self.value = value
        self.frequency = frequency
        self.children = children or []

    def __repr__(self):
        return f"MinHeapNode({repr(self.value)}, {self.frequency}, {self.children})"

    def __add__(self, other: MinHeapNode):
        if not isinstance(other, MinHeapNode):
            raise TypeError
        return MinHeapNode(self.value+other.value, self.frequency+other.frequency, [self, other])

    def __getitem__(self, key):
        return self.children[key]

    @staticmethod
    def print_tree(node, prefix="", is_last=True):
        # Choose branch characters based on whether it is the last child
        connector = "└── " if is_last else "├── "
        print(prefix + connector + str(node.value))
        
        # Update prefix for children
        prefix += "    " if is_last else "│   "
        
        # Recursively print all children
        for i, child in enumerate(node.children):
            is_last_child = (i == len(node.children) - 1)
            MinHeapNode.print_tree(child, prefix, is_last_child)

class MinHeap:
    def __init__(self, nodes: list[MinHeapNode]):
        self.nodes = nodes
        self.sort()

    def __len__(self):
        return len(self.nodes)

    def insert(self, node: MinHeapNode):
        for i, n in enumerate(self.nodes):
            if node.frequency <= n.frequency:
                self.nodes.insert(i, node)
                return
        self.nodes.append(node)

    @staticmethod
    def from_counter(counter: Counter):
        return MinHeap([MinHeapNode(k, v) for k,v in counter.ascending()])

    @staticmethod
    def from_file(filename):
        tally = Counter()

        with open(filename, "r") as file:
            data = file.read()
            for c in data:
                tally.increment(c)

        return MinHeap.from_counter(tally)

    def sort(self):
        while len(self) > 1:
            node1 = self.nodes.pop(0)
            node2 = self.nodes.pop(0)
            combined_nodes = node1 + node2
            self.insert(combined_nodes)      

    def to_dict(self):
        def _helper(node: MinHeapNode, code: str, d: dict):
            if not node.children:
                d[node.value] = code
                return
            for i in range(2):
                _helper(node.children[i], code+str(i), d)
        d = {}
        _helper(self.nodes[0], '', d)
        return d

def save_compressed_file(filename, huffman_dict, bitstring):
    padding = -(len(bitstring) % -8)
    bitstring += ("0"*padding)
    if len(bitstring) % 8 != 0:
        raise RuntimeError(f"Output_str % 8 = {len(bitstring) % 8}")
    num_bytes = len(bitstring) // 8
    output_bin = int(bitstring, 2).to_bytes(num_bytes)

    header_bytes = json.dumps(huffman_dict).encode("utf-8")

    metadata = struct.pack(">IB", len(header_bytes), padding)
    with open(filename, "wb") as file:
        file.write(metadata)
        file.write(header_bytes)
        file.write(output_bin)

def read_compressed_file(filename):
    with open(filename, "rb") as file:
        metadata_size = struct.calcsize(">IB")
        header_len, padding = struct.unpack(">IB", file.read(metadata_size))

        header_bytes = file.read(header_len)
        huffman_dict = json.loads(header_bytes.decode("utf-8"))

        payload_bytes = file.read()

    bitstring = "".join(f"{byte:08b}" for byte in payload_bytes)
    if padding > 0:
        bitstring = bitstring[:-padding]

    return huffman_dict, bitstring

def encrypt_file(input_filename, output_filename):
    tally = Counter()

    with open(input_filename, "r") as file:
        data = file.read()
        for c in data:
            tally.increment(c)

    heap = MinHeap.from_counter(tally)
    header = heap.to_dict()

    bitstring = ""
    for c in data:
        bitstring += header[c]

    save_compressed_file(output_filename, header, bitstring)   

def decrypt_file(input_filename, output_filename):
    huffman_dict, bitstring = read_compressed_file(input_filename)
    decrypt_dict = {code:char for char,code in huffman_dict.items()}
    output = ""

    code = ""
    i = 0
    while i < len(bitstring):
        code += bitstring[i]
        if code in decrypt_dict:
            output += decrypt_dict[code]
            code = ""
        i += 1

    with open(output_filename, "w") as output_file:
        output_file.write(output)

if __name__ == "__main__":
    context = ParseContext(sys.argv, 1)

    root = RootNode().with_children([
        LiteralNode("-e").with_child(
            CaptureNode("input_filename").with_child(
                CaptureNode("output_filename").with_child(
                    FunctionNode(encrypt_file)
                )
            )
        ),
        LiteralNode("-d").with_child(
            CaptureNode("input_filename").with_child(
                CaptureNode("output_filename").with_child(
                    FunctionNode(decrypt_file)
                )
            )
        )
    ])

    root.parse(context)