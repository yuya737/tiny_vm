from collections import defaultdict

class Dependency_Graph:
    def __init__(self):
        self.graph = defaultdict(list)

    def addEdge(self, vertex, incident_vertex):
        self.graph[vertex].append(incident_vertex)

    def topologicalSort(self):
        def helper(v, visited, stack):
            visited.append(v)

            for i in self.graph[v]:
                if i not in visited:
                    helper(i, visited, stack)

            stack.insert(0, v)

        visited = []
        stack = []

        for k in list(self.graph):
            if k not in visited:
                helper(k, visited, stack)

        return stack
