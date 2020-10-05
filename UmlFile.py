import pygraphviz as gv


class UmlNamespace:
    def __init__(self):
        self.namespace = []

    def add(self, n):
        self.namespace.append(n)

    def __hash__(self):
        return hash("::".join(self.namespace))

    def __eq__(self, other):
        return "::".join(self.namespace) == "::".join(other.namespace)

    def __str__(self):
        return "::".join(self.namespace)

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
        return "\t" + self.visibility + self.name + " : " + str(self.type) + "\n"


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
    LINK_TYPE_MAP = {
        'inherit': '<|--',
        'aggregation': 'o--',
        'composition': '*--'
    }

    def __init__(self, id, namespace, name):
        self.id = id
        self.name = name
        self.namespace = namespace
        self.parents = set()
        self.parentsDistant = set()
        self.attributes = {}
        self.methods = {}

    def get_namespace_name(self):
        return '::'.join(self.namespace.namespace + [self.name])

    def __str__(self):
        r = ""
        for ns in self.namespace.namespace:
            r += "namespace " + ns + " {\n"

        r += "class " + self.name
        pdc = self.parentsDistant.copy()
        for p in self.parents:
            if p.namespace != self.namespace:
                pdc.add(p.get_namespace_name())
        if len(pdc) != 0:
            r += "<<" + ', '.join(pdc) + ">>"
        r += " {\n"

        for a in self.attributes.values():
            if a.type.umlClass is None:
                r += str(a)
            else:
                if a.type.umlClass.namespace != self.namespace:
                    r += str(a)

        for m in self.methods.values():
            r += str(m) + "\n"

        r += "}\n"

        for useless in self.namespace.namespace:
            r += "}\n"

        for p in self.parents:
            if p.namespace == self.namespace:
                r += p.get_namespace_name() + " --|> " + self.get_namespace_name() + "\n"

        for a in self.attributes.values():
            if a.type.umlClass is not None and a.type.umlClass.namespace == self.namespace:
                r += a.type.umlClass.get_namespace_name() + " <--o " + self.get_namespace_name() + "\n"

        return r


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

    def __str__(self):
        r = "@startuml\nset namespaceSeparator ::\nhide members\n"
        for key, value in self.umlClass.items():
            r += str(value)
            r += "\n"

        r += "@enduml\n"
        return r

    def draw(self, path):

        database = {}

        for c in self.umlClass.values():
            if c.namespace not in database:
                database[c.namespace] = []

            database[c.namespace].append(c)

        # plantUml per namespace
        for k, d in database.items():
            r = "@startuml\nset namespaceSeparator ::\n"
            for c in d:
                r += str(c)
            r += "@enduml\n"
            with open(path + str(k) + ".puml", "w") as f:
                f.write(r)
        # The compact diagram
        A = gv.AGraph(directed=True, strict=True, rankdir="LR")
        A.node_attr["shape"] = "tab"
        # A.graph_attr["splines"] = "ortho"
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
        A.draw(path + "compact.svg", prog='dot')

        # The all diagram
        for k, d in database.items():
            A = gv.AGraph(directed=True, strict=False)
            A.node_attr["shape"] = "record"
            # A.graph_attr["splines"] = "ortho"

            for c in d:
                text = c.name
                e = []
                for p in c.parents:
                    if p.namespace == c.namespace:
                        A.add_edge(p.id, c.id, arrowtail="empty", dir="back")
                    else:
                        e.append(p.get_namespace_name())

                if e:
                    text = '\\n'.join(e) + '|' + text

                e = []

                for a in c.attributes.values():
                    if a.type.umlClass is not None and a.type.umlClass.namespace == c.namespace:
                        A.add_edge(a.type.umlClass.id, c.id, arrowhead="ediamond", arrowtail="normal", dir="both")
                    else:
                        e.append(a.name)

                if e:
                    text += '||' + '\\n'.join(e)

                e = []

                for m in c.methods.values():
                    e.append(str(m))

                if e:
                    text += '|' + '\\n'.join(e)

                A.add_node(c.id, label= '{' + text + '}')

            A.layout()
            A.draw(path + str(k) + "_gv.svg", prog='dot')


def get_cluster_name(namespace):
    return 'cluster_' + '_'.join(namespace)
