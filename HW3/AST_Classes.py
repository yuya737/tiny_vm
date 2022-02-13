from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type, Union

import class_hierarchy

ch: class_hierarchy.RootObjClass

class ASTNode:
    """Abstract base class"""
    def __init__(self) -> None:
        self.children: List[ASTNode] = []

    def r_eval(self, local_var_dict: Dict[str, str]) -> Optional[List[str]]:
        """Evaluate for value"""
        raise NotImplementedError(f"r_eval not implemented for node type {self.__class__.__name__}")

    def l_eval(self) -> Optional[List[str]]:
        """Evaluate for value"""
        raise NotImplementedError(f"r_eval not implemented for node type {self.__class__.__name__}")

    def c_eval(self, true_branch: str, false_branch: str, local_var_dict: Dict[str, str]) -> Optional[List[str]]:
        raise NotImplementedError(f"c_eval not implemented for node type {self.__class__.__name__}")

    def type_eval(self, local_var_dict: Dict[str, str]) -> Optional[str]:
        raise NotImplementedError(f"type_eval not implemented for node type {self.__class__.__name__}")

    def pretty_label(self) -> str:
        raise NotImplementedError(f"pretty_label not implemented for node type {self.__class__.__name__}")


LAB_COUNT = 0
def new_label(prefix: str) -> str:
    global LAB_COUNT
    LAB_COUNT += 1
    return f"{prefix}_{LAB_COUNT}"

def pretty_helper(node: ASTNode, level: int, indent_str: str) -> List[str]:
    print(node)
    # print(node.children)
    if len(node.children) == 0:
        return [indent_str*level, node.pretty_label(), '\n']

    l = [indent_str*level, node.pretty_label(), '\n']
    # print(l)
    for n in node.children:
        l += pretty_helper(n, level+1, indent_str)

    return l

def pretty_print(RootNode: ASTNode) -> None:
    print(''.join(pretty_helper(RootNode, 0, '  ')))

class RootNode(ASTNode):
    """Sequence of statements"""
    def __init__(self, program: ASTNode):
        super().__init__()
        self.children.append(program)

    def r_eval(self, local_var_dict: Dict[str, str]):
        """Evaluate for value"""
        program = self.children[0]
        return program.r_eval(local_var_dict)

    def type_eval(self, local_var_dict: Dict[str, str]):
        """Evaluate for value"""
        program = self.children[0]
        return program.type_eval(local_var_dict)

    def pretty_label(self) -> str:
        return "RootNode"


class IfNode(ASTNode):
    """if cond then block else block"""
    def __init__(self, condpart: ASTNode, thenpart: ASTNode, elsepart: ASTNode) -> None:
        super().__init__()
        self.children.append(condpart)
        self.children.append(thenpart)
        if elsepart:
            self.children.append(elsepart)

    def r_eval(self, local_var_dict: Dict[str, str]):
        """Evaluate for value"""
        if len(self.children) == 2:
            condpart, thenpart = self.children
            elsepart = []
        else:
            condpart, thenpart, elsepart = self.children

        then_label = new_label("then")
        else_label = new_label("else")
        endif_label = new_label("endif")
        iftest = condpart.c_eval(then_label, else_label, local_var_dict)
        thenblock = thenpart.r_eval(local_var_dict)
        elseblock = elsepart.r_eval(local_var_dict) if elsepart else []
        return (iftest
                + [then_label + ":"]
                + thenblock
                + [f"\tjump {endif_label}"]
                + [else_label + ":"]
                + elseblock
                + [endif_label + ":"])

    def type_eval(self, local_var_dict: Dict[str, str]):
        # Make sure that the condpart actually evaluates to a Boolean
        if len(self.children) == 2:
            condpart, thenpart = self.children
            thenpart.type_eval(local_var_dict)
        else:
            condpart, thenpart, elsepart = self.children

            var_dict_before_if = local_var_dict

            var_dict_after_then = local_var_dict.copy()
            thenpart.type_eval(var_dict_after_then)

            var_dict_after_else = local_var_dict.copy()
            elsepart.type_eval(var_dict_after_else)

            # Construct new var_dict as a union of items. When there is an overlap assign the LCA
            new_dict = var_dict_after_then.copy()

            for var in var_dict_after_else:
                if var in new_dict:
                    new_dict[var] = ch.find_LCA(var_dict_after_else[var], new_dict[var])
                else:
                    new_dict[var] = var_dict_after_else[var]

            # Update the passed local_var_dict (only need to add items, var_dict never loses items here)
            for new_item in new_dict:
                local_var_dict[new_item] = new_dict[new_item]

        if condpart.type_eval(local_var_dict) != "Boolean":
            raise TypeError("If statement expects the condition to return a Boolean")

        return None


    def pretty_label(self) -> str:
        if len(self.children) == 2:
            return "IfNode"
        else:
            return "IfElseNode"


class WhileNode(ASTNode):
    """if cond then block else block"""
    def __init__(self, condpart: ASTNode, statementblock: ASTNode):
        super().__init__()
        self.children.append(condpart)
        self.children.append(statementblock)

    def r_eval(self, local_var_dict: Dict[str, str]):
        """Evaluate for value"""
        condpart, statementblock = self.children
        loophead = new_label("loop_head")
        looptest = new_label("loop_test")
        nextStmt = new_label("done")

        block = statementblock.r_eval(local_var_dict)

        whiletest = condpart.c_eval(loophead, nextStmt, local_var_dict)
        return ([f'jump {looptest}']
                + [loophead + ":"]
                + block
                + [looptest + ":"]
                + whiletest
                + [nextStmt + ":"])

    def type_eval(self, local_var_dict: Dict[str, str]):
        condpart, statementblock = self.children
        statementblock.type_eval(local_var_dict)

        if condpart.type_eval(local_var_dict) != "Boolean":
            raise TypeError("If statement expects the condition to return a Boolean")
        return None

    def pretty_label(self) -> str:
        return "WhileNode"


class MethodcallNode(ASTNode):
    """Method call node"""
    def __init__(self, caller: ASTNode, m_name: str, argslist: List[ASTNode]):
        super().__init__()
        self.children.append(caller)
        self.children += argslist
        self.m_name = m_name

    def r_eval(self, local_var_dict: Dict[str, str]):
        caller = self.children[0]
        caller_type = caller.type_eval(local_var_dict)
        return ([subitem for args in self.children[1:] for subitem in args.r_eval(local_var_dict)]
                + caller.r_eval(local_var_dict)
                + [f'\tcall {caller_type}:{self.m_name}'])

    def type_eval(self, local_var_dict: Dict[str, str]):
        caller, *argslist = self.children
        caller_type = caller.type_eval(local_var_dict)
        # args_types = [subitem for arg in argslist for subitem in arg.type_eval()]
        args_types = [args.type_eval(local_var_dict) for args in argslist]

        # print(caller.r_eval())
        # print('In methodcall type eval')
        quackClassEntry = ch.find_class(caller_type)

        # Make sure this function exists
        quackFunctionEntry = [entry for entry in quackClassEntry.methods_list if entry.method_name == self.m_name]
        if not quackFunctionEntry:
            raise NotImplementedError(f'Function {self.m_name} for {caller_type} is not defined')

        quackFunction = quackFunctionEntry[0]

        # Make sure that the arguments are the right type
        if args_types != quackFunction.params:
            raise TypeError(f'Function {self.m_name} for {caller_type} expects {quackFunction.params} but got {args_types}')

        return quackFunction.ret

    def c_eval(self, true_branch: str, false_branch: str, local_var_dict: Dict[str, str]) -> List[str]:
        bool_code = self.r_eval(local_var_dict)
        return bool_code + [f"\tjump_if  {true_branch}", f"\tjump {false_branch}"]

    def pretty_label(self) -> str:
        return f"MethodcallNode: {self.m_name}"


class StatementNode(ASTNode):
    """Statement node"""
    def __init__(self, statement: ASTNode):
        super().__init__()
        self.children.append(statement)

    def r_eval(self, local_var_dict: Dict[str, str]):
        return self.children[0].r_eval(local_var_dict)

    def type_eval(self, local_var_dict: Dict[str, str]):
        self.children[0].type_eval(local_var_dict)
        return None

    def get_field_variables(self, field_var_list: Dict[str, str], temp_local_var_dict: Dict[str, str]):
        for child in self.children:
            if isinstance(child, AssignmentNode):
                child.get_field_variables(field_var_list, temp_local_var_dict)

    def pretty_label(self) -> str:
        return "StatementNode"

class StatementBlockNode(ASTNode):
    """Statement node"""
    def __init__(self, statement_block: List[ASTNode]):
        super().__init__()
        self.children = statement_block

    def r_eval(self, local_var_dict: Dict[str, str]):
        return [subitem for statement in self.children for subitem in statement.r_eval(local_var_dict)]

    def type_eval(self, local_var_dict: Dict[str, str]):
        for statement in self.children:
            statement.type_eval(local_var_dict)
        return None

    def pretty_label(self) -> str:
        return f"StatementBlockNode: length {len(self.children)}"

class ProgramNode(ASTNode):
    """Class  Node"""
    def __init__(self, class_list: List[ASTNode], statement_list: List[ASTNode]):
        super().__init__()
        # self.children.append(program)
        self.children = class_list
        self.children += statement_list
        # self.num_classes = len(class_list)

    def r_eval(self, local_var_dict: Dict[str, str]):
        return ([subitem for child in self.children for subitem in child.r_eval(local_var_dict)])

    def type_eval(self, local_var_dict: Dict[str, str]):
        for child in self.children:
            child.type_eval(local_var_dict)
        return None

    def pretty_label(self) -> str:
        return "ProgramNode"

class ClassNode(ASTNode):
    """Class Node"""
    def __init__(self, class_signature: ASTNode, class_body: ASTNode):
        super().__init__()
        self.children.append(class_signature)
        self.children.append(class_body)

        # Add class to class hierachy
        class_name = class_signature.class_name
        super_class = class_signature.super_class
        methods_list = []
        for method_node in class_body.children[class_body.num_constructor_statement:]:
            method_name = method_node.method_name
            # children[0] gets the formal_args node
            params_list = method_node.children[0].arg_types
            ret_type = method_node.ret_type
            methods_list.append(class_hierarchy.QuackClassMethod(method_name, params_list, ret_type))
        field_var_list = {}

        # Make a temporary local_var_dict to get the types of the fields - add every variable passed into the constructor
        temp_local_var_dict = {}
        class_formal_args = self.children[0].children[0]
        for index, constructor_parameter in enumerate(class_formal_args.arg_names):
            temp_local_var_dict[constructor_parameter] = class_formal_args.arg_types[index]
        class_body.get_field_variables(field_var_list, temp_local_var_dict)

        new_class_to_add = class_hierarchy.QuackClass(class_name, super_class, methods_list, field_var_list)
        breakpoint()
        global ch
        ch.add_class_to_hierarchy(new_class_to_add)
        class_hierarchy.pretty_print(ch)
        # breakpoint()


    def r_eval(self, local_var_dict: Dict[str, str]):
        class_signature, class_body = self.children
        return (class_signature.r_eval(local_var_dict) +
                class_body.r_eval(local_var_dict, len(class_signature.children[0].arg_names)))

    def type_eval(self, local_var_dict: Dict[str, str]):
        for child in self.children:
            child.type_eval(local_var_dict)

    def pretty_label(self) -> str:
        return "ClassNode"

class ClassBodyNode(ASTNode):
    """Class Body Node"""
    def __init__(self, statement_list: List[ASTNode], method_list: List[ASTNode]):
        super().__init__()
        self.children += statement_list
        self.children += method_list
        self.num_constructor_statement = len(statement_list)

    def r_eval(self, local_var_dict: Dict[str, str], num_constructor_arguments: int):
        ret = []
        statement_list = self.children[:self.num_constructor_statement]
        method_list = self.children[self.num_constructor_statement:]

        # Constructor lines
        for statement in statement_list:
            ret += statement.r_eval(local_var_dict)

        ret += ['\tload $', f'\treturn {num_constructor_arguments}']

        # Class Methods
        for method in method_list:
            ret += method.r_eval(local_var_dict)

        return ret

    def type_eval(self, local_var_dict: Dict[str, str]):
        return None

    # Get a list of field variables
    def get_field_variables(self, field_var_list: Dict[str, str], temp_local_var_dict: Dict[str, str]) -> None:
        for possible_field_assignment in self.children[:self.num_constructor_statement]:
            possible_field_assignment.get_field_variables(field_var_list, temp_local_var_dict)

    def pretty_label(self) -> str:
        return "ClassBodyNode"

# class ReturnNode(ASTNode):
#     """Return statment node"""
#     def __init__(self, rexp: ASTNode):
#         super().__init__()
#         self.children.append(rexp)

#     def r_eval(self, local_var_dict: Dict[str, str]):
#         return



class ClassSignatureNode(ASTNode):
    """Class Signature Node"""
    def __init__(self, class_name: str,  formal_args: ASTNode, super_class: str):
        super().__init__()
        self.class_name = class_name
        self.children.append(formal_args)
        if super_class:
            self.super_class = super_class
        else:
            self.super_class = "Obj"

    def r_eval(self, local_var_dict: Dict[str, str]):

        # Write out the class declaration
        class_declaration = [f'.class {self.class_name}:{self.super_class}']

        # Write out class fieds
        field_declaration = []
        for variable in ch.find_class(self.class_name).fields_list:
            field_declaration += [f'.field {variable}']

        # Write out method forward declarations
        method_forward_declaration = []
        for method in ch.find_class(self.class_name).methods_list:
            method_forward_declaration += [f'.method {method.method_name} forward']

        # Write out constructor declaration
        constructor_declaration = ['.method $constructor']
        formal_args = self.children[0]
        if formal_args.arg_names:
            constructor_declaration += [f".args {','.join(formal_args.arg_names)}"]

        return class_declaration + field_declaration + method_forward_declaration + constructor_declaration

    def type_eval(self, local_var_dict: Dict[str, str]) -> None:
        formal_args = self.children[0]
        # Make sure every constructor parameter has a valid class
        for constructor_parameter_type in formal_args.arg_types:
            if not ch.find_class(constructor_parameter_type):
                raise TypeError(f'{constructor_parameter_type} defined in constructor is an invalid type')
        # If a super_class is defined, make sure it actually exists
        if self.super_class and not ch.find_class(self.super_class):
            raise TypeError(f'{self.class_name} specifies {self.super_class} as its super class but it does not exist')
        return None


    def pretty_label(self) -> str:
        return "ClassSignatureNode"

class ClassMethodNode(ASTNode):
    """Class Method"""
    def __init__(self, method_name: str, formal_args: ASTNode, ret_type: str, statement_block: ASTNode):
        super().__init__()
        self.children.append(formal_args)
        self.children.append(statement_block)
        self.method_name = method_name
        self.ret_type = ret_type

    def r_eval(self, local_var_dict: Dict[str, str]):
        formal_args, statement_block = self.children

        args_declaration = [f".args {','.join(formal_args.arg_names)}"] if formal_args.arg_names else []

        # Add local arguments to local_var_dict
        for i in range(len(formal_args.arg_names)):
            local_var_dict[formal_args.arg_names[i]] = formal_args.arg_types[i]

        # Get the list of local variables this block defines (maybe this is shady...)
        statement_block_instructions = statement_block.r_eval(local_var_dict)

        # Write out method declaration
        method_declaration = [f'.method {self.method_name}']

        # Write out local variable declaration
        local_var_declaration = []
        local_vars_in_function = list(local_var_dict.keys())
        local_vars_in_function = [item for item in local_vars_in_function if item not in formal_args.arg_names]
        if local_vars_in_function:
            local_var_declaration = [f".local {','.join(local_vars_in_function)}"]

        # Write out return line
        return_line = [f'\treturn {len(self.children[0].arg_names)}']

        return method_declaration + args_declaration + local_var_declaration + statement_block_instructions +  return_line

    def type_eval(self, local_var_dict: Dict[str, str]):
        return None

    def pretty_label(self) -> str:
        return "ClassMethod Node"



class FormalArgsNode(ASTNode):
    """Formal args Node"""
    def __init__(self, lst: List[str]):
        super().__init__()
        self.arg_names = lst[::2]
        self.arg_types = lst[1::2]

    def r_eval(self, local_var_dict: Dict[str, str]):
        return None

    def type_eval(self, local_var_dict: Dict[str, str]):
        for arg_type in self.arg_types:
            if not ch.find_class(arg_type):
                raise ValueError(f'{arg_type} is an invalid type')
        return None

    def pretty_label(self) -> str:
        return f'Formal Args Node: {self.arg_names}'


class ProgramNode(ASTNode):
    """Program  Node"""
    def __init__(self, class_list: List[ASTNode], statement_list: List[ASTNode]):
        super().__init__()
        # self.children.append(program)
        self.children = class_list
        self.children += statement_list
        # self.num_classes = len(class_list)

    def r_eval(self, local_var_dict: Dict[str, str]) -> List[str]:
        return ([subitem for child in self.children for subitem in child.r_eval(local_var_dict)])

    def type_eval(self, local_var_dict: Dict[str, str]) -> None:
        for child in self.children:
            child.type_eval(local_var_dict)
        return None

    def pretty_label(self) -> str:
        return "ProgramNode"

class MethodargsrecurNode(ASTNode):
    """Methodargs recur Node"""
    def __init__(self, methodargs: ASTNode, rexp: ASTNode):
        super().__init__()
        self.children.append(methodargs)
        self.children.append(rexp)

    def r_eval(self, local_var_dict: Dict[str, str]) -> List[str]:
        methodargs, rexp = self.children
        return (methodargs.r_eval(local_var_dict)
                + rexp.r_eval(local_var_dict))

    def type_eval(self, local_var_dict: Dict[str, str]) -> None:
        methodargs, rexp = self.children
        methodargs.type_eval(local_var_dict)
        rexp.type_eval(local_var_dict)
        return None

    def pretty_label(self) -> str:
        return "MethodargsRecurNode"


class MethodargsNode(ASTNode):
    """Methodargs  Node"""
    def __init__(self, rexp: ASTNode):
        super().__init__()
        self.children.append(rexp)

    def r_eval(self, local_var_dict: Dict[str, str]) -> List[str]:
        return (self.children[0].r_eval())

    def type_eval(self, local_var_dict: Dict[str, str]) -> None:
        self.children[0].type_eval(local_var_dict)
        return None

    def pretty_label(self) -> str:
        return "MethodargsNode"

class AssignmentNode(ASTNode):
    """Assignment Node"""
    def __init__(self, lexp: ASTNode, var_type: str, rexp: ASTNode):
        super().__init__()
        self.children.append(lexp)
        self.children.append(rexp)
        self.var_type = var_type

    def r_eval(self, local_var_dict: Dict[str, str]) -> List[str]:
        lexp, rexp = self.children
        return (rexp.r_eval(local_var_dict)
                + lexp.l_eval())
                # + [f'\tstore {storing_to[0]}'])

    def type_eval(self, local_var_dict: Dict[str, str]) -> None:
        lexp, rexp = self.children

        actual_type = rexp.type_eval(local_var_dict)
        declared_type = self.var_type
        prev_inferred_type = local_var_dict.get(lexp.variable, None)
        newly_inferred_type = None

        # Add to var_dict if this is the first encounter
        if not prev_inferred_type:
            local_var_dict[lexp.variable] = actual_type

        # If we inferred a type before ...
        if prev_inferred_type:
            new_candidate_type = ch.find_LCA(prev_inferred_type, actual_type)
            local_var_dict[lexp.variable] = new_candidate_type
            newly_inferred_type = new_candidate_type
        else:
            newly_inferred_type = actual_type

        # If a type was declared, make sure it is an actual class and make sure that it is legal with the newly inferred type
        if declared_type:
            if not ch.find_class(declared_type):
                raise TypeError(f'Declared type {declared_type} is an invalid class')
            if not ch.is_legal_assignment(declared_type, newly_inferred_type):
                raise TypeError(f'Assignment declared {declared_type} but inferred {newly_inferred_type}')

        lexp.type_eval(local_var_dict)
        rexp.type_eval(local_var_dict)

        return None

    def get_field_variables(self, field_var_list: Dict[str, str], temp_local_var_dict: Dict[str, str]):
        lexp, rexp = self.children
        if isinstance(lexp, ThisReferenceLexpNode):
            field_var_list[lexp.value] = rexp.type_eval(temp_local_var_dict)



    def pretty_label(self) -> str:
        return f"AssignmentNode {self.var_type}"


class RexpNode(ASTNode):
    """Rexp Node"""
    def __init__(self, rexp: ASTNode):
        super().__init__()
        self.children.append(rexp)

    def r_eval(self, local_var_dict: Dict[str, str]) -> List[str]:
        return self.children[0].r_eval(local_var_dict)

    def c_eval(self, true_branch: str, false_branch: str, local_var_dict: Dict[str, str]) -> List[str]:
        return self.children[0].c_eval(true_branch, false_branch, local_var_dict)

    def type_eval(self, local_var_dict: Dict[str, str]) -> str:
        return self.children[0].type_eval(local_var_dict)

    def pretty_label(self) -> str:
        return "RexpNode"


class BareLexpNode(ASTNode):
    """BareLexp Node"""
    def __init__(self, lexp: str):
        super().__init__()
        self.value = lexp

    def r_eval(self, local_var_dict: Dict[str, str]):
        return self.value

    def l_eval(self):
        return [f'\tstore {self.value}']

    def type_eval(self, local_var_dict: Dict[str, str]):
        return local_var_dict[self.value]

    def pretty_label(self) -> str:
        return f"BareLexpNode {self.value}"

class ThisReferenceLexpNode(ASTNode):
    """ThisLexp Node"""
    def __init__(self, field_variable: str):
        super().__init__()
        self.value = field_variable

    def r_eval(self, local_var_dict: Dict[str, str]):
        return ['\tload $', f'\tload_field $:{self.value}']

    def l_eval(self):
        return ['\tload $', f'\tstore_field $:{self.value}']

    def get_value(self) -> List[str]:
        return self.value

    def type_eval(self, local_var_dict: Dict[str, str]):
        return None

    def pretty_label(self) -> str:
        return f"ThisLexpNode {self.value}"

class FieldReferenceLexpNode(ASTNode):
    """FieldLexp Node"""
    def __init__(self, field_variable: str):
        super().__init__()
        self.value = field_variable

    def r_eval(self, local_var_dict: Dict[str, str]):
        return self.value

    def get_value(self) -> List[str]:
        return self.value

    def type_eval(self, local_var_dict: Dict[str, str]):
        return None

    def pretty_label(self) -> str:
        return f"FieldLexpNode {self.value}"


class VarReferenceNode(ASTNode):
    """VarReferecnce Node"""
    def __init__(self, variable: ASTNode):
        super().__init__()
        self.variable = variable

    def r_eval(self, local_var_dict: Dict[str, str]):
        return [f'\tload {self.variable}']

    def l_eval(self):
        return [f'\tstore {self.variable}']

    # def c_eval(self, true_branch: str, false_branch: str) -> List[str]

    def type_eval(self, local_var_dict: Dict[str, str]) -> str:
        if self.variable not in local_var_dict:
            raise ValueError(f'{self.variable} is referenced before assignment')
        return local_var_dict[self.variable]

    def c_eval(self, true_branch: str, false_branch: str, local_var_dict: Dict[str, str]) -> List[str]:
        bool_code = self.r_eval(local_var_dict)
        return bool_code + [f"\tjump_if  {true_branch}", f"\tjump {false_branch}"]

    def pretty_label(self) -> str:
        return f'VarReferenceNode: {self.variable}'


class ConstNode(ASTNode):
    """Constant"""
    def __init__(self, value: str, value_type: str):
        super().__init__()
        self.value = value
        self.value_type = value_type

    def r_eval(self, local_var_dict: Dict[str, str]) -> List[str]:
        return [f"\tconst {self.value}"]

    def type_eval(self, local_var_dict: Dict[str, str]) -> str:
        return self.value_type

    def pretty_label(self) -> str:
        return f"ConstNode {self.value}"


class BoolNode(ASTNode):
    """Boolean """
    def __init__(self, value: str):
        super().__init__()
        self.value = value

    def r_eval(self, local_var_dict: Dict[str, str]) -> List[str]:
        return [f"\tconst {self.value}"]

    def c_eval(self, true_branch: str, false_branch: str, local_var_dict: Dict[str, str]) -> List[str]:
        bool_code = self.r_eval(local_var_dict)
        return bool_code + [f"\tjump_if  {true_branch}", f"\tjump {false_branch}"]

    def type_eval(self, local_var_dict: Dict[str, str]) -> str:
        return "Boolean"

    def pretty_label(self) -> str:
        return f"BoolNode {self.value}"


class ComparisonNode(ASTNode):
    """Comparisons are the leaves of conditional branches
    and can also return boolean values
    """
    def __init__(self, left: ASTNode, right: ASTNode, comp_op: str):
        super().__init__()
        self.children.append(left)
        self.children.append(right)
        self.comp_op = comp_op


    def r_eval(self, local_var_dict: Dict[str, str]) -> List[str]:
        """Called if we want a boolean VALUE rather than a branch"""
        left, right = self.children
        left_code = left.r_eval(local_var_dict)
        right_code = right.r_eval(local_var_dict)
        caller_type = left.type_eval(local_var_dict)

        if self.comp_op == "==":
            return right_code + left_code + [f'\tcall {caller_type}:EQUALS']
        if self.comp_op == "<":
            return right_code + left_code + [f'\tcall {caller_type}:LESS']
        if self.comp_op == ">":
            return right_code + left_code + [f'\tcall {caller_type}:MORE']
        if self.comp_op == "<=":
            return right_code + left_code + [f'\tcall {caller_type}:ATMOST']
        if self.comp_op == ">=":
            return right_code + left_code + [f'\tcall {caller_type}:ATLEAST']

    def type_eval(self, local_var_dict: Dict[str, str]) -> str:
        left, right = self.children

        caller_type = left.type_eval(local_var_dict)
        quackClassEntry = ch.find_class(caller_type)

        # If equals, make sure that the equals exists
        if self.comp_op == "==":

            # Make sure this function exists
            quackFunctionEntry = [entry for entry in quackClassEntry.methods_list if entry.method_name == "EQUALS"]
            if not quackFunctionEntry:
                raise NotImplementedError(f'Function EQUALS for {caller_type} is not defined')

        if self.comp_op == "<":

            # Make sure this function exists
            quackFunctionEntry = [entry for entry in quackClassEntry.methods_list if entry.method_name == "LESS"]
            if not quackFunctionEntry:
                raise NotImplementedError(f'Function LESS for {caller_type} is not defined')

        if self.comp_op == ">":

            # Make sure this function exists
            quackFunctionEntry = [entry for entry in quackClassEntry.methods_list if entry.method_name == "MORE"]
            if not quackFunctionEntry:
                raise NotImplementedError(f'Function MORE for {caller_type} is not defined')

        if self.comp_op == "<=":

            # Make sure this function exists
            quackFunctionEntry = [entry for entry in quackClassEntry.methods_list if entry.method_name == "ATMOST"]
            if not quackFunctionEntry:
                raise NotImplementedError(f'Function ATMOST for {caller_type} is not defined')

        if self.comp_op == ">=":

            # Make sure this function exists
            quackFunctionEntry = [entry for entry in quackClassEntry.methods_list if entry.method_name == "ATLEAST"]
            if not quackFunctionEntry:
                raise NotImplementedError(f'Function ATLEAST for {caller_type} is not defined')

        return "Boolean"

    def c_eval(self, true_branch: str, false_branch: str, local_var_dict: Dict[str, str]) -> List[str]:
        bool_code = self.r_eval(local_var_dict)
        return bool_code + [f"\tjump_if  {true_branch}", f"\tjump {false_branch}"]

    def pretty_label(self) -> str:
        return f"ComparisonNode: {self.comp_op}"

class AndNode(ASTNode):
    """Boolean and, short circuit; can be evaluated for jump or for boolean value"""
    def __init__(self, left: ASTNode, right: ASTNode):
        super().__init__()
        self.children.append(left)
        self.children.append(right)

    # FIXME: Needs r_eval to allow production of boolean value

    def r_eval(self, local_var_dict: Dict[str, str]) -> List[str]:
        left, right = self.children
        return (left.r_eval(local_var_dict) + right.r_eval(local_var_dict) + ['\tcall Boolean:AND'])

    def c_eval(self, true_branch: str, false_branch: str, local_var_dict: Dict[str, str]) -> List[str]:
        """Use in a conditional branch"""
        continue_label = new_label("and")
        left, right = self.children
        return (left.c_eval(continue_label, false_branch, local_var_dict)
                + [continue_label + ":"]
                + right.c_eval(true_branch, false_branch, local_var_dict)
                )

    def type_eval(self, local_var_dict: Dict[str, str]) -> str:
        return "Boolean"


    def pretty_label(self) -> str:
        return "AndNode"


class OrNode(ASTNode):
    """Boolean or, short circuit; can be evaluated for jump or for boolean value"""
    def __init__(self, left: ASTNode, right: ASTNode):
        super().__init__()
        self.children.append(left)
        self.children.append(right)

    # FIXME: Needs r_eval to allow production of boolean value

    def r_eval(self, local_var_dict: Dict[str, str]) -> List[str]:
        left, right = self.children
        return (left.r_eval(local_var_dict) + right.r_eval(local_var_dict) + ['\tcall Boolean:OR'])

    def c_eval(self, true_branch: str, false_branch: str, local_var_dict: Dict[str, str]) -> List[str]:
        """Use in a conditional branch"""
        continue_label = new_label("and")
        left, right = self.children
        return (left.c_eval(true_branch, continue_label, local_var_dict)
                + [continue_label + ":"]
                + right.c_eval(true_branch, false_branch, local_var_dict)
                )

    def type_eval(self, local_var_dict: Dict[str, str]) -> str:
        return "Boolean"

    def pretty_label(self) -> str:
        return "OrNode"


class NotNode(ASTNode):
    """Boolean or, short circuit; can be evaluated for jump or for boolean value"""
    def __init__(self, statement: ASTNode):
        super().__init__()
        self.children.append(statement)

    # FIXME: Needs r_eval to allow production of boolean value

    def r_eval(self, local_var_dict: Dict[str, str]) -> List[str]:
        statement = self.children[0]
        return (statement.r_eval(local_var_dict) + ['\tcall Boolean:NOT'])

    def c_eval(self, true_branch: str, false_branch: str, local_var_dict: Dict[str, str]) -> List[str]:
        """Use in a conditional branch"""
        statement = self.children[0]
        return statement.c_eval(false_branch, true_branch, local_var_dict)

    def type_eval(self, local_var_dict: Dict[str, str]) -> str:
        return "Boolean"

    def pretty_label(self) -> str:
        return "NotNode"

def parse_builtin_classes(builtinclass_json):
    global ch
    ch = class_hierarchy.parse_builtin_classes(builtinclass_json)

def print_class_hierarchy():
    global ch
    class_hierarchy.pretty_print(ch)
