import pygraphviz as gv
import os


class UmlNamespace:
    def __init__(self):
        self.namespace = []

    def __hash__(self):
        return hash("::".join(self.namespace))

    def __eq__(self, other):
        return "::".join(self.namespace) == "::".join(other.namespace)

    def __str__(self):
        return "::".join(self.namespace)

    def add(self, n):
        self.namespace.append(n)

    def copy(self):
        r = UmlNamespace()
        r.namespace = self.namespace.copy()
        return r


class UmlType:
    def __init__(self, spelling, umlClass):
        self.const = False
        self.spelling = spelling
        self.umlClass = umlClass

    def __str__(self):
        return self.spelling


class UmlAttribubte:
    def __init__(self, name, type, visibility):
        self.name = name
        self.type = type
        self.visibility = visibility

    def __str__(self):
        return self.visibility + self.name + " : " + str(self.type)


class UmlMethod:
    def __init__(self, name, returnType, argumentTypes, visibility):
        self.name = name
        self.returnType = returnType
        self.argumentTypes = argumentTypes
        self.visibility = visibility

    def __str__(self):
        if self.returnType == "void":
            return self.visibility + self.name
        else:
            return self.visibility + self.name + " : " + self.returnType


class UmlClass:

    def __init__(self, id, namespace, name):
        self.id = id
        self.name = name
        self.namespace = namespace
        self.parents = set()
        self.parentsDistant = set()
        self.attributes = {}
        self.methods = {}

    def __str__(self):
        return '::'.join(self.namespace.namespace + [self.name])


class UmlFile:
    LINK_TYPE_MAP = {
        'inherit': '<|--',  # héritage (is a)
        'composition': '<--*',  # une classe dépendante (has a) --> nested class
        'aggregation': '<--o',  # une classe indépendante (has a) --> &
        'association': '<--',  # un pointer (knows a) --> *
        'dependency': '<..'  # est utilisé dans les entete (uses a)
    }

    def __init__(self):
        self.umlClass = {}
        self.methods = {}

    def draw(self, path):

        database = {}

        full = gv.AGraph(directed=True, strict=False, overlap=False)
        full.node_attr["shape"] = "record"
        for c in self.umlClass.values():
            if c.namespace not in database:
                database[c.namespace] = []

            database[c.namespace].append(c)

            cluster = full
            namespace = []
            for n in c.namespace.namespace:
                namespace.append(n)
                cl = cluster.get_subgraph(get_cluster_name(namespace))
                if cl is None:
                    cl = cluster.add_subgraph(name=get_cluster_name(namespace), label=n)
                cluster = cl
            cluster.add_node(c.id)

        # The compact diagram
        A = gv.AGraph(directed=True, strict=True, rankdir="LR")
        A.node_attr["shape"] = "tab"
        for k, d in database.items():
            label = "<<TABLE BORDER=\"0\" CELLBORDER=\"0\" CELLSPACING=\"0\"><TR><TD>" + str(k) + "</TD></TR><TR><TD><TABLE BORDER=\"0\" CELLBORDER=\"1\" >"
            for c in d:
                id = "\"" + c.id.replace("<", "").replace(">", "") + "\""
                name = c.name.replace("<", "&lt;").replace(">", "&gt;")
                if c.parentsDistant:
                    name = ', '.join(c.parentsDistant) + "<BR/>" + name
                label += "<TR><TD port=" + id + ">" + name + "</TD></TR>"
                for p in c.parents:
                    if p.namespace != c.namespace:
                        A.add_edge(str(p.namespace), str(c.namespace), arrowtail="empty", dir="back")
            A.add_node(k, label=label + "</TABLE></TD></TR></TABLE>>")
        A.layout()
        if not os.path.exists(path):
            os.makedirs(path)
        A.draw(path + "/compact.svg", prog='dot')

        # The all diagram
        for k, d in database.items():
            A = gv.AGraph(directed=True, strict=False, overlap=False)
            A.node_attr["shape"] = "record"

            # A.graph_attr["splines"] = "ortho"

            for c in d:
                text = c.name
                e = []
                for p in c.parents:
                    full.add_edge(p.id, c.id, arrowtail="empty", dir="back")
                    if p.namespace == c.namespace:
                        A.add_edge(p.id, c.id, arrowtail="empty", dir="back")
                    else:
                        e.append(str(p))

                if e:
                    text = '\\n'.join(e) + '|' + text

                e = []

                for a in c.attributes.values():
                    if a.type.umlClass is not None:
                        full.add_edge(a.type.umlClass.id, c.id, arrowhead="ediamond", arrowtail="normal", dir="both")
                    if a.type.umlClass is not None and a.type.umlClass.namespace == c.namespace:
                        A.add_edge(a.type.umlClass.id, c.id, arrowhead="ediamond", arrowtail="normal", dir="both")
                    else:
                        e.append(str(a))

                if e:
                    text += '|' + '\\n'.join(e)

                e = []

                for m in c.methods.values():
                    e.append(str(m))

                if e:
                    text += '|' + '\\n'.join(e)
                A.add_node(c.id, label='{' + text.replace('<', '\\<').replace('>', '\\>') + '}')
                full.get_node(c.id).attr["label"] = '{' + text.replace('<', '\\<').replace('>', '\\>') + '}'

            # p = None
            # for n in [path] + k.namespace:
            #     if p is None:
            #         p = n
            #     else:
            #         p += "/" + n
            #     if not os.path.exists(p):
            #         os.makedirs(p)

            A.unflatten('-f -l 40 -c 40')
            # A.write(p + "/" + str(k) + ".dot")
            A.layout(prog='dot')
            A.draw(path + "/" + str(k).replace('::', '_') + ".svg")
        full.unflatten('-f -l 400 -c 400')
        # full.write(path + "/main.dot")
        full.layout(prog='dot')
        full.draw(path + "/main.svg")


def get_cluster_name(namespace):
    return 'cluster_' + '_'.join(namespace)
