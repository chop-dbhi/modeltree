def print_tree(tree, file=None, node=None, depth=0, toks=None):
    """Traverses the entire tree and prints a hierarchical view to `file` or
    returns a string if not no file is specified.
    """
    if toks is None:
        toks = []

    if node is None:
        node = tree.root_node

    if node:
        toks.append('.' * depth * 4)
        toks.append('{0}\n'.format(node.model_name))

    if node.children:
        for child in node.children:
            print_tree(tree, file, child, depth + 1, toks)

    if depth == 0:
        if file is None:
            return ''.join(toks)
        file.write(''.join(toks))
