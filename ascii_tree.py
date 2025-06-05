from scipy.cluster.hierarchy import linkage, to_tree
from scipy.spatial.distance import squareform

def ascii_dendrogram(ncd_mat, labels):
    # linkage espera matriz condensada
    dist_vec = squareform(ncd_mat, checks=False)
    Z = linkage(dist_vec, method='average')
    tree, _ = to_tree(Z, rd=True)
    lines = []
    def build_ascii(node, prefix="", is_last=True):
        if node.is_leaf():
            lines.append(f"{prefix}{'└─' if is_last else '├─'}{labels[node.id]}")
        else:
            lines.append(f"{prefix}{'└─' if is_last else '├─'}+ [{node.dist:.2f}]")
            children = [node.get_left(), node.get_right()]
            for i, child in enumerate(children):
                build_ascii(child, prefix + ("   " if is_last else "│  "), i == len(children)-1)
    build_ascii(tree, "", True)
    return "\n".join(lines)
