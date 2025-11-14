import networkx


def try_get_first_node(g, wire, ending_contacts):
    result = 0
    for node in g.nodes:
        if node not in ending_contacts:
            result = node
            break
    if result == 0:
        if len(ending_contacts) > 0:
            result = ending_contacts[0]
        else:
            raise Exception(wire, g.nodes, ending_contacts, 'По какой-то причине не было найдено первого узла у жилы!')
    return result


def make_montage_list(g, wire, ending_contacts):
    result = networkx.Graph()
    if len(g.nodes) == 2:  # См комментарий в find_min_weight
        n1, n2 = g.nodes
        result.add_edge(n1, n2, weight=g[n1][n2]['weight'])
        return result

    root = try_get_first_node(g, wire, ending_contacts)
    n0, n1 = root, root
    while len(result) < len(g):
        node0, weight0 = find_min_weight(g, n0, result, ending_contacts)
        node1, weight1 = find_min_weight(g, n1, result, ending_contacts)
        if weight0 < weight1:
            result.add_edge(n0, node0, weight=weight0)
            n0 = node0
        else:
            result.add_edge(n1, node1, weight=weight1)
            n1 = node1

    return result


def make_path(G):
    leafs = find_leaf(G)
    return networkx.dfs_edges(G, source=leafs[0])


def find_min_weight(G, root, checked, ending_contacts):
    inf = 999999
    weight = inf
    result = 0
    for dev in G[root]:
        if dev not in checked and G[root][dev]['weight'] < weight and dev not in ending_contacts:
            result = dev
            weight = G[root][dev]['weight']
    if result == 0:
        for dev in G[root]:
            if dev not in checked and G[root][dev]['weight'] < weight:
                result = dev
                if root in ending_contacts:
                    weight = inf  # Блокируем будущий поиск ближайших соседей для концевого контакта!
                                  # ToDo некорректный результ для жили из 2х верших, каждая
                                  # из которых присутствует в массива ending_contacts. Для устранения этого
                                  # в make_montage_list добавлен случай обработки только 2х вершин
                else:
                    weight = G[root][dev]['weight']
    if result == 0:
        raise Exception(G, root, G[root], checked, ending_contacts, 'Не найден узел с минимальным весом!')

    return result, weight


def find_leaf(G):
    result = [x for x in G.nodes() if G.degree(x)==1]
    return result


def read_wires(graph_dir, wires):
    result = {}
    for wire in wires.keys():
        result[wire] = networkx.read_gml(
            get_wire_gml_filename(graph_dir, wire)
        )
    return result


def get_wire_gml_filename(graph_dir, wire):
    return f"{graph_dir}/{wire}.gml"


def save_wire(graph_dir, wire, devices, closet_graph):
    graph_wire = networkx.Graph()
    for _ in range(len(devices)):
        u = devices.pop()
        for v in devices:
            w = networkx.dijkstra_path_length(closet_graph, u, v, 'weight')
            graph_wire.add_edge(u, v, weight=w)
    networkx.write_gml(
        graph_wire,
        get_wire_gml_filename(graph_dir, wire)
    )


def save_graph_wires(graph_dir, wires, closet_graph):
    for wire, devices in wires.items():
        if len(devices) == 1:
            raise Exception(wire, devices, "У жилы только один контакт!")
        save_wire(graph_dir, wire, devices, closet_graph)


def generate_graph_devices(graph_dir, wires, closet_graph, from_files=False):
    if from_files == False:
        save_graph_wires(graph_dir, wires, closet_graph)
    return read_wires(graph_dir, wires)