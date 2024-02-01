from memobj import WindowsProcess

from arrtype.memory import HashNode

HASH_CALL_PATTERN = rb"\xE8....\x85\xF6\x8B\x68\x04\x74\x04\x3B\xF0\x74\x06\xFF\x15....\x3B\xFD\x74\x3F\x85\xF6\x75\x06"

PROCESS_NAME = "Pirate.exe"

def _get_root_node(process: WindowsProcess) -> HashNode:
    # for now this pattern is unique in WizardGraphicalClient.exe
    # note that there is an ambiguous match in the bug reporter,
    # which is why we restrict the scan here
    hash_call_addr = process.scan_one(HASH_CALL_PATTERN, module=PROCESS_NAME)

    # E8 [B2 43 00 00]
    call_offset: int = process.read_formatted(hash_call_addr + 1, "i")  # type: ignore

    # 5 is the length of the call instruction
    call_addr = hash_call_addr + call_offset + 5

    # 84 1D [04 D2 44 02]
    hash_tree_offset: int = process.read_formatted(call_addr + 0x28 + 2, "i")  # type: ignore

    # subtract 0x4 because we're grabing at a test of the initialized flag which is 0x4 in
    hash_tree_offset -= 0x4

    # 0x28 is start of the lea instruction and 6 is the length of it
    #hash_tree_addr = call_addr + 0x28 + hash_tree_offset + 6

    pointer = process.read_formatted(hash_tree_offset, process.pointer_format_string)
    #address = process.read_formatted(pointer, process.pointer_format_string)

    return HashNode(address=pointer, process=process).parent


def _get_children_nodes(node: HashNode, nodes: set):
    nodes.add(node)

    if node.is_leaf is False:
        if left_node := node.left:
            if left_node not in nodes:
                _get_children_nodes(left_node, nodes)
        if right_node := node.right:
            if right_node not in nodes:
                _get_children_nodes(right_node, nodes)

    return nodes


def _read_all_nodes(root_node: HashNode):
    nodes = set()

    first_node = root_node.parent
    return _get_children_nodes(first_node, nodes)


def get_hash_nodes(process: WindowsProcess) -> set[HashNode]:
    root_node = _get_root_node(process)
    return _read_all_nodes(root_node)


def get_type_tree() -> dict[str, HashNode]:
    process = WindowsProcess.from_name(PROCESS_NAME)

    nodes = get_hash_nodes(process)

    hash_map = {}

    for node in nodes:
        if node.is_leaf:
            continue

        hash_map[node.node_data.name] = node

    return hash_map


if __name__ == "__main__":
    tree = get_type_tree()
    print(f"{len(tree)=}")
    
    print(tree)
