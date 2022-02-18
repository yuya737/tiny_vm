from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type, Union
import json

class QuackClassMethod():
    def __init__(self, method_name: str, params: List[str], ret: str):
        self.method_name = method_name
        self.params = params
        self.ret = ret


class QuackClass():
    def __init__(self, class_name: str, super_class: str, methods_list: List[QuackClassMethod], fields_list: Dict[str, str]):
        self.class_name = class_name
        self.super_class = super_class
        self.methods_list = methods_list
        self.fields_list = fields_list
        self.children: List[QuackClass] = []


class RootObjClass(QuackClass):
    def __init__(self):
        Obj_methods = [QuackClassMethod("STR", [], "String"),
                       QuackClassMethod("PRINT", [], "Nothing"),
                       QuackClassMethod("equals", ["Obj"], "Boolean")
                       ]
        super().__init__("Obj", "Obj", Obj_methods, {})

    def get_path_to_subclass_helper(self, cur_node: QuackClass, class_name: str, path_so_far: List[str]) -> bool:
        path_so_far.append(cur_node.class_name)

        if cur_node.class_name == class_name:
            return True

        if any([self.get_path_to_subclass_helper(child, class_name, path_so_far) for child in cur_node.children]):
            return True

        path_so_far.pop()
        return False


    def get_path_to_subclass(self, class_name: str) -> List[str]:
        ret = []
        assert(self.get_path_to_subclass_helper(self, class_name, ret))
        # self.get_path_to_subclass_helper(self, class_name, ret)
        return ret

    def find_LCA(self, class_name_1: str, class_name_2: str) -> str:
        # None is the bottom type so...
        if not class_name_1:
            return class_name_2
        if not class_name_2:
            return class_name_1
        path_to_class_1 = self.get_path_to_subclass(class_name_1)
        path_to_class_2 = self.get_path_to_subclass(class_name_2)

        # print(path_to_class_1)
        # print(path_to_class_2)
        last_common_index = -1
        for index, (i, j) in enumerate(zip(path_to_class_1, path_to_class_2)):
            if i == j:
                last_common_index += 1
            else:
                break
        return path_to_class_1[last_common_index]

    # Make sure that type 'actual_class' can be assigned to 'expected_class'
    def is_legal_assignment(self, expected_class: str, actual_class: str) -> bool:
        path_to_expected_class = self.get_path_to_subclass(expected_class)
        path_to_actual_class = self.get_path_to_subclass(actual_class)

        # Return if path_to_actual_class starts with path_to_expected_class. In other words, if actual_class is a subclass of expected_class
        return path_to_actual_class[:len(path_to_expected_class)] == path_to_expected_class

    def is_legal_invocation(self, class_name: str, method_name: str, passed_types: List[str]):
        class_entry = self.find_class(class_name)
        # Make sure the class exists
        if not class_entry:
            raise TypeError(f'Function call on {class_name} was made but {class_name} does not exist')

        # Make sure this function exists
        quackFunctionEntry = [entry for entry in class_entry.methods_list if entry.method_name == method_name]
        if not quackFunctionEntry:
            raise ValueError(f'Function call {method_name} on {class_name} was made but {method_name} is undefined for {class_name}')

        expected_param_args = quackFunctionEntry[0].params
        # Make sure we got the right number of arguments
        if len(expected_param_args) != len(passed_types):
            raise SyntaxError(f'Function call {method_name} on {class_name} expected {len(expected_param_args)} arguments but received {len(passed_types)}')

        # Make sure each argument is valid
        for index, (expected, actual) in enumerate(zip(expected_param_args, passed_types)):
            if not self.is_legal_assignment(expected, actual):
                raise SyntaxError(f'Function call {method_name} on {class_name} expected {expected} on argument number {index} but received {actual}')


    def find_class_helper(self, cur_node: QuackClass, class_name: str) -> Union[QuackClass, None]:
        if cur_node.class_name == class_name:
            return cur_node

        child_res = [self.find_class_helper(child, class_name) for child in cur_node.children]
        if any(child_res):
            return next(item for item in child_res if item)

        return None

    def find_class(self, class_name: str) -> QuackClass:
        return self.find_class_helper(self, class_name)


    def add_class_to_hierarchy_helper(self, cur_node: QuackClass, node_to_add: QuackClass) -> None:
        if node_to_add.super_class == cur_node.class_name:
            cur_node.children.append(node_to_add)
        else:
            for child in cur_node.children:
                self.add_class_to_hierarchy_helper(child, node_to_add)

    def add_class_to_hierarchy(self, node_to_add: QuackClass) -> None:
        self.add_class_to_hierarchy_helper(self, node_to_add)

def pretty_helper(node: QuackClass, level: int, indent_str: str):
    # print(node)
    # print(node.children)
    if len(node.children) == 0:
        return [indent_str*level, node.class_name, '\n']

    l = [indent_str*level, node.class_name, '\n']
    # print(l)
    for n in node.children:
        l += pretty_helper(n, level+1, indent_str)

    return l

def pretty_print(RootNode: QuackClass):
    print(''.join(pretty_helper(RootNode, 0, '  ')))



def parse_builtin_classes(path_to_json: str) -> QuackClass:
    with open(path_to_json) as f:
        builtin_classes = json.load(f)

    root_node = RootObjClass()

    # Ignore the first Obj class
    for builtin_class in [*builtin_classes][1:]:
        # breakpoint()
        cur_class = builtin_classes[builtin_class]

        super_class = cur_class['super']
        fields_list = cur_class['fields']
        methods_list = []

        for class_method in [*cur_class['methods']][1:]:
            methods_list.append(QuackClassMethod(class_method, cur_class['methods'][class_method]['params'], cur_class['methods'][class_method]['ret']))

        new_class = QuackClass(builtin_class, super_class, methods_list, fields_list)
        root_node.add_class_to_hierarchy(new_class)

    return root_node



if __name__ == "__main__":
    root = parse_builtin_classes('../builtinclass.json')
    pretty_print(root)
    root.add_class_to_hierarchy(QuackClass("TEST", "Int", [], []))
    pretty_print(root)

    a = root.find_class('String')
    breakpoint()
    # print(root.find_LCA('TEST2', 'TEST4'))



