import sys
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type, Union
from lark import Lark, Transformer, v_args, Visitor, Tree, Token
from lark.tree import pydot__tree_to_png
from dataclasses import dataclass
import class_hierarchy

    # program: statement -> program
    #     | program statement -> program_recur

quack_grammar = """
    ?start: program -> root

    program: class* statement*

    class: class_signature class_body

    class_signature: "class" IDENT "(" formal_args ")" ["extends" IDENT]

    formal_args: [ IDENT ":" IDENT ("," IDENT ":" IDENT)*]

    class_body: "{" statement* method* "}"

    method: "def" IDENT "(" formal_args ")" [":" IDENT] statement_block

    statement_block: "{" statement* "}"

    statement: rexp ";"
        | assignment ";"
        | ifstmt
        | whilestmt
        | "return" rexp ";"

    ifstmt: "if" rexp statement_block [("else" statement_block)] -> ifstmt
        | "if" rexp statement_block ("elif" rexp statement_block)+ "else" statement_block -> ifelseifstmt

    whilestmt: "while" rexp statement_block

    methodcall: rexp "." IDENT "(" methodargs? ")"

    methodargs: rexp ("," rexp)*

    assignment: lexp [":" type] "=" rexp

    ?type: IDENT

    rexp: "true"            -> true
        | "false"           -> false
        | methodcall
        | constant
        | lexp              -> var_reference
        | IDENT "(" methodargs? ")"
        | rexp "or" rexp -> _or
        | "not" rexp -> _not
        | rexp "<" rexp -> lt
        | rexp ">" rexp -> gt
        | rexp "<=" rexp -> leq
        | rexp ">=" rexp -> geq
        | rexp "==" rexp -> eq
        | rexp "+" product   -> add
        | rexp "-" product   -> sub
        | "-" rexp -> neg
        | "(" rexp ")"
        | product


    ?product: rexp
        | product "*" rexp  -> mul
        | product "/" rexp  -> div

    lexp: IDENT             -> lexp
        | rexp "." IDENT


    ?constant: INT       -> number
        | ESCAPED_STRING    -> string


    IDENT: /[_a-zA-Z][_a-zA-Z0-9]*/
    %import common.CNAME -> NAME
    %import common.INT
    %import common.ESCAPED_STRING
    %import common.WS

    %ignore WS
"""
    # ?arth_expr:
    #     | rexp "+" rexp -> add
    #     | rexp "-" rexp -> sub
    #     | rexp "*" rexp -> mul
    #     | rexp "/" rexp -> div
    #     | "-" rexp -> neg
    #     | "(" arth_expr ")"


    # ?sum: product
    #     | sum "+" product   -> add
    #     | sum "-" product   -> sub

    # ?product: atom
    #     | product "*" atom  -> mul
    #     | product "/" atom  -> div

    # ?atom: constant
    #     | "-" atom          -> neg
    #     | lexp              -> var_reference
    #     | "(" sum ")"

ch = None
# tc = None
# var_dict: Dict[str, str] = {}

class ASTNode:
    def __init__(self) -> None:
        self.children: List[ASTNode] = []

    """Abstract base class"""
    def r_eval(self, local_var_dict: Dict[str, str]) -> List[str]:
        """Evaluate for value"""
        raise NotImplementedError(f"r_eval not implemented for node type {self.__class__.__name__}")

    def c_eval(self, true_branch: str, false_branch: str, local_var_dict: Dict[str, str]) -> List[str]:
        raise NotImplementedError(f"c_eval not implemented for node type {self.__class__.__name__}")

    def type_eval(self, local_var_dict: Dict[str, str]) -> str:
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

    def r_eval(self, local_var_dict: Dict[str, str]) -> List[str]:
        """Evaluate for value"""
        program = self.children[0]
        return program.r_eval(local_var_dict)

    def type_eval(self, local_var_dict: Dict[str, str]) -> str:
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

    def r_eval(self, local_var_dict: Dict[str, str]) -> List[str]:
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

    def type_eval(self, local_var_dict: Dict[str, str]) -> None:
        # Make sure that the condpart actually evaluates to a Boolean
        if len(self.children) == 2:
            condpart, thenpart = self.children
            thenpart.type_eval(local_var_dict)
        else:
            condpart, thenpart, elsepart = self.children

            var_dict_before_if = self.local_var_dict

            var_dict_after_then = self.local_var_dict.copy()
            thenpart.type_eval(var_dict_after_then)

            var_dict_after_else = self.local_var_dict.copy()
            elsepart.type_eval(var_dict_after_else)

            # Construct new var_dict as a union of items. When there is an overlap assign the LCA
            new_dict = var_dict_after_then.copy()
            for var in var_dict_after_else:
                if var in new_dict:
                    new_dict[var] = ch.find_LCA(var_dict_after_else[var], new_dict[var])
                else:
                    new_dict[var] = var_dict_after_else[var]
            # var_dict = new_dict
            self.local_var_dict = new_dict

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

    def r_eval(self, local_var_dict: Dict[str, str]) -> List[str]:
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

    def type_eval(self, local_var_dict: Dict[str, str]) -> None:
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

    def r_eval(self, local_var_dict: Dict[str, str]) -> List[str]:
        caller = self.children[0]
        return ([subitem for args in self.children[1:] for subitem in args.r_eval(local_var_dict)]
                + caller.r_eval(local_var_dict)
                + [f'\tcall Int:{self.m_name}'])

    def type_eval(self, local_var_dict: Dict[str, str]) -> str:
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

    def r_eval(self, local_var_dict: Dict[str, str]) -> List[str]:
        return self.children[0].r_eval(local_var_dict)

    def type_eval(self, local_var_dict: Dict[str, str]) -> None:
        self.children[0].type_eval(local_var_dict)
        return None

    def pretty_label(self) -> str:
        return "StatementNode"

class StatementBlockNode(ASTNode):
    """Statement node"""
    def __init__(self, statement_block: List[ASTNode]):
        super().__init__()
        self.children = statement_block

    def r_eval(self, local_var_dict: Dict[str, str]) -> List[str]:
        return [subitem for statement in self.children for subitem in statement.r_eval(local_var_dict)]

    def type_eval(self, local_var_dict: Dict[str, str]) -> None:
        for statement in self.children:
            statement.type_eval(local_var_dict)
        return None

    def pretty_label(self) -> str:
        return f"StatementBlockNode: length {len(self.children)}"

class ClassNode(ASTNode):
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
                + [f'\tstore {lexp.r_eval(local_var_dict)}'])

    def type_eval(self, local_var_dict: Dict[str, str]) -> None:
        lexp, rexp = self.children

        actual_type = rexp.type_eval(local_var_dict)
        declared_type = self.var_type
        prev_inferred_type = local_var_dict.get(lexp.value, None)
        newly_inferred_type = None

        # Add to var_dict if this is the first encounter
        if not prev_inferred_type:
            local_var_dict[lexp.value] = actual_type

        # If we inferred a type before ...
        if prev_inferred_type:
            new_candidate_type = ch.find_LCA(prev_inferred_type, actual_type)
            local_var_dict[lexp.value] = new_candidate_type
            newly_inferred_type = new_candidate_type
        else:
            newly_inferred_type = actual_type

        # If a type was declared, make sure that it is legal with the newly inferred type
        if declared_type and not ch.is_legal_assignment(declared_type, newly_inferred_type):
            raise TypeError(f'Assignment declared {declared_type} but inferred {newly_inferred_type}')

        lexp.type_eval(local_var_dict)
        rexp.type_eval(local_var_dict)

        return None

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


class LexpNode(ASTNode):
    """Lexp Node"""
    def __init__(self, lexp: str):
        super().__init__()
        self.value = lexp

    def r_eval(self, local_var_dict: Dict[str, str]) -> List[str]:
        return self.value

    def get_value(self) -> List[str]:
        return self.value

    def type_eval(self, local_var_dict: Dict[str, str]) -> None:
        return None

    def pretty_label(self) -> str:
        return f"LexpNode {self.value}"


class VarReferenceNode(ASTNode):
    """VarReferecnce Node"""
    def __init__(self, variable: ASTNode):
        super().__init__()
        self.variable = variable.get_value()

    def r_eval(self, local_var_dict: Dict[str, str]) -> List[str]:
        return [f'\tload {self.variable}']

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
        bool_code = self.r_eval()
        return bool_code + [f"\tjump_if  {true_branch}", f"\tjump {false_branch}"]

    def type_eval(self) -> str:
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


# class MakeAssemblyTree(Transformer):
class MakeAssemblyTree(Transformer):

    def __init__(self, file):
        self.vars = {}
        self.file = file
        self.var_dict = {}
        self.Input_output_dtypes_dict = {}
        self.final_instr = []

        # Functions to populate Input_output_dtypes:
        # neg, add, sub, mul, div
        # self.Input_output_dtypes_dict['neg'] = [Input_output_dtypes(['Int'], 'Int')]
        # self.Input_output_dtypes_dict['add'] = [Input_output_dtypes(['Int', 'Int'], 'Int'),
        #                                         Input_output_dtypes(['String', 'String'], 'String')]
        # self.Input_output_dtypes_dict['sub'] = [Input_output_dtypes(['Int', 'Int'], 'Int')]
        # self.Input_output_dtypes_dict['mul'] = [Input_output_dtypes(['Int', 'Int'], 'Int')]
        # self.Input_output_dtypes_dict['div'] = [Input_output_dtypes(['Int', 'Int'], 'Int')]

    def write_to_file(self):
        with open(self.file, 'w') as file:
            print(self.var_dict)
            file.write('.class Main:Obj\n')
            file.write('\n')
            file.write('.method $constructor\n')
            file.write(f'.local {",".join(self.var_dict.keys())}\n')
            for line in self.final_instr:
                file.write(line)
            file.write('\thalt\n')
            file.write('\treturn 0\n')

    def root(self, lst) -> ASTNode:
        print(f'In number {lst}')
        return RootNode(lst[0])

    def number(self, lst) -> ASTNode:
        print(f'In number {lst}')
        return ConstNode(int(lst[0]), 'Int')

    def string(self, lst) -> ASTNode:
        print(f'In string {lst}')
        return ConstNode(str(lst[0]), 'String')

    def true(self, lst) -> ASTNode:
        print(f'In true {lst}')
        return BoolNode("true")

    def false(self, lst) -> ASTNode:
        print(f'In true {lst}')
        return BoolNode("false")

    def methodcall(self, lst) -> ASTNode:
        print(f'In methodcall {lst}')
        caller, m_name, *methodargs = lst
        return MethodcallNode(caller, m_name.value, methodargs)

    def statement(self, lst) -> ASTNode:
        print(f'In statement {lst}')
        return StatementNode(lst[0])

    def statement_block(self, lst) -> ASTNode:
        # breakpoint()
        print(f'In statement_block {lst}')
        return StatementBlockNode(lst)

    def methodargs_recur(self, lst) -> ASTNode:
        print(f'In methodargs_recur {lst}')
        methodargs, constant = lst
        return MethodargsrecurNode(methodargs, constant)

    def methodargs(self, lst) -> ASTNode:
        print(f'In methodargs {lst}')
        return MethodargsNode(lst[0])

#     def program_recur(self, lst) -> ASTNode:
#         print(f'In program_recur {lst}')
#         program, statement = lst
#         return ProgramrecurNode(program, statement)

    def program(self, lst) -> ASTNode:
        class_list = [item for item in lst if isinstance(item, ClassNode)]
        program_list = lst[len(class_list):]
        print(f'In program {lst}')
        return ProgramNode(class_list, program_list)

    def assignment(self, lst) -> ASTNode:
        lexp, *var_type, rexp = lst
        var_type = var_type[0]
        print(var_type)
        if var_type:
            var_type = var_type.value
        print(f'In assignment lexp:{lexp}, type:{var_type}, rexp:{rexp}')
        return AssignmentNode(lexp, var_type, rexp)

    def ifstmt(self, lst) -> ASTNode:
        condpart, thenpart, elsepart = lst
        print(f'In ifstmt {lst}')
        return IfNode(condpart, thenpart, elsepart)

    def ifelseifstmt(self, lst) -> ASTNode:
        condpart, thenpart, *elifblock, elsepart = lst
        print(f'In ifelseifstmt {lst}')
        elif_node = IfNode(elifblock[-2], elifblock[-1], elsepart)

        # Number of additional elifs to handle
        num_elifs = len(elifblock) / 2 - 1
        counter = 2
        while num_elifs > 0:
            elif_node = IfNode(elifblock[-2*counter], elifblock[-2*counter + 1], elif_node)
            num_elifs -= 1
            counter += 1
        return IfNode(condpart, thenpart, elif_node)

    def whilestmt(self, lst) -> ASTNode:
        condpart, statementblock = lst
        print(f'In whilestmt {lst}')
        return WhileNode(condpart, statementblock)


    def _or(self, lst) -> ASTNode:
        left, right = lst
        print(f'In OR {left}, {right}')
        return OrNode(left, right)

    def _and(self, lst) -> ASTNode:
        left, right = lst
        print(f'In OR {left}, {right}')
        return AndNode(left, right)

    def _not(self, lst) -> ASTNode:
        statement = lst[0]
        print(f'In NOT {statement}')
        return NotNode(statement)

    def eq(self, lst) -> ASTNode:
        left, right = lst
        print(f'In eq {left}, {right}')
        return ComparisonNode(left, right, "==")

    def lt(self, lst) -> ASTNode:
        left, right = lst
        print(f'In lt {left}, {right}')
        return ComparisonNode(left, right, "<")

    def gt(self, lst) -> ASTNode:
        left, right = lst
        print(f'In gt {left}, {right}')
        return ComparisonNode(left, right, ">")

    def geq(self, lst) -> ASTNode:
        left, right = lst
        print(f'In geq {left}, {right}')
        return ComparisonNode(left, right, ">=")

    def leq(self, lst) -> ASTNode:
        left, right = lst
        print(f'In leq {left}, {right}')
        return ComparisonNode(left, right, "<=")


    def type(self, lst) -> str:
        print(f'In type NAME:{lst[0]}')
        return lst[0].value

    def lexp(self, lst) -> ASTNode:
        print(f'In lexp NAME:{lst[0]}')
        return LexpNode(lst[0].value)

    def rexp(self, lst) -> ASTNode:
        print(f'In rexp NAME:{lst[0]}')
        return RexpNode(lst[0])

    def var_reference(self, lst) -> ASTNode:
        print(f'In var_reference var:{lst[0]}')
        return VarReferenceNode(lst[0])

    # # Check if the current function arguments are valid. If so, return receiver type and return type
    # def check_if_valid_func_invocation(self, func_name: str, input_type_list: List[str]):
    #     for candidate in self.Input_output_dtypes_dict[func_name]:
    #         # If matching one exists return it
    #         if input_type_list == candidate.input_dtype:
    #             return (True, candidate.input_dtype[0], candidate.output_dtype)

    #     return (False, None, None)

    # def neg(self, expression: Instr_dtype_pair) -> Instr_dtype_pair:
    def neg(self, lst) -> ASTNode:
        val = lst
        print(f'In neg: {val}')
        return MethodcallNode(ConstNode(0, 'Int'), "MINUS", val)

    def add(self, lst) -> ASTNode:
        val1, val2 = lst
        print(f'In add: {val1}, {val2}')
        return MethodcallNode(val1, "PLUS", [val2])

    def sub(self, lst) -> ASTNode:
        val1, val2 = lst
        print(f'In sub: {val1}, {val2}')
        return MethodcallNode(val1, "MINUS", [val2])

    def mul(self, lst) -> ASTNode:
        val1, val2 = lst
        print(f'In mul: {val1}, {val2}')
        return MethodcallNode(val1, "TIMES", [val2])

    def div(self, lst) -> ASTNode:
        val1, val2 = lst
        print(f'In mul: {val1}, {val2}')
        return MethodcallNode(val1, "DIVIDE", [val2])

def type_check(RootNode: ASTNode) -> Dict[str, str]:
    var_dict: Dict[str, str] = {}
    RootNode.type_eval(var_dict)
    temp_var_dict = var_dict.copy()
    print('Variables after first pass', var_dict)
    count = 1
    while True:
        print(f'In type_check iteration number: {count}')
        RootNode.type_eval(var_dict)
        print(f'Variables after pass numer: {count}', var_dict)
        count += 1
        if temp_var_dict == var_dict:
            break
        else:
            temp_var_dict = var_dict.copy()
    print('Finished Type Checking')
    return var_dict

def write_to_file(RootNode: ASTNode, output_asm: str, var_dict: Dict[str, str]) -> None:
    instr = RootNode.r_eval(var_dict)
    print(instr)
    with open(output_asm, 'w') as f:
        f.write('.class Main:Obj\n')
        f.write('\n')
        f.write('.method $constructor\n')
        var_list = ','.join(var_dict.keys())
        if var_list:
            f.write(f'.local {var_list}\n')
        for i in instr:
            f.write(i)
            f.write('\n')
        f.write('\thalt\n')
        f.write('\treturn 0\n')



def main(quack_file, output_asm, builtinclass_json):
    # quack_parser = Lark(quack_grammar, parser='lalr')
    quack_parser = Lark(quack_grammar)
    quack = quack_parser.parse
    with open(quack_file) as f:
        input_str = f.read()
    print(input_str)
    tree = MakeAssemblyTree(output_asm)
    print('------------------------------------------------------')
    print(quack(input_str).pretty())
    print('------------------------------------------------------')
    ast = tree.transform(quack(input_str))
    print('------------------------------------------------------')
    pydot__tree_to_png(quack(input_str), 'a.png')
    global ch
    ch = class_hierarchy.parse_builtin_classes(builtinclass_json)
    print('Printing Class Hierarchy')
    class_hierarchy.pretty_print(ch)
    print('------------------------------------------------------')
    print('Printing Transformed AST')
    pretty_print(ast)
    print('------------------------------------------------------')
    var_dict = type_check(ast)
    print('Printing Final Var_dict')
    print(var_dict)
    print('------------------------------------------------------')
    write_to_file(ast, output_asm, var_dict)



if __name__ == '__main__':
    if len(sys.argv) != 4:
        print('Usage: lark_parser.py [input_quack_file] [path/to/output.asm] [path/to/builtinclass.json]')
        sys.exit(1)
    main(sys.argv[1], sys.argv[2], sys.argv[3])
