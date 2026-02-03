from src.elements import LineCommand
from src.elements import Text


class GraphView:
    def __init__(self, leavies):
        self._leavies = self._make_coordinate(leavies)
        
    def _make_coordinate(self, leavies):
        result = {}
        for leaf in leavies:
            result[leaf.full_name] = leaf.center
        return result

    def _is_node(self, check):
        return type(check) is int
    
    def _is_leaf(self, check):
        return not self._is_node(check)
    
    def _get_node_coordinate(self, nodes, node_number):
        return nodes[node_number].center
        
    def _get_leaf_coordinate(self, leaf):
        return self._leavies[leaf]


    def plot(self, nodes, closet_graph, font_size):
        res = {}
        lisp_text = []
        lisp_line = []
        for e in closet_graph.edges:
            line = []
            for p in e:
                if self._is_node(p):
                    c = self._get_node_coordinate(nodes, p)
                else:
                    c = self._get_leaf_coordinate(p)
                    
                if str(p) not in res:
                    res[str(p)] = 1
                    size = font_size[0] if self._is_node(p) else font_size[1]
                    lisp_text += [Text(c, str(p), size, 0, '_MC')]
                line.append(c)
            lisp_line += [LineCommand(line[0], line[1])]
        return lisp_line + lisp_text