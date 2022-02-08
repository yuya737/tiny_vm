import sys
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type, Union
from lark import Lark, Transformer, v_args, Visitor, Tree, Token
from lark.tree import pydot__tree_to_png
from dataclasses import dataclass
import class_hierarchy
import type_checker

quack_grammar = """
    ?start: program -> root

    program: statement -> program
        | program statement -> program_recur

    statement_block: "{" statement* "}"

    statement: rexp ";"
        | assignment ";"
        | ifstmt

    ifstmt: "if" rexp statement_block [("else" statement_block)] -> ifstmt
        | "if" rexp statement_block ("elif" rexp statement_block)+ "else" statement_block -> ifelseifstmt


    methodcall: rexp "." NAME "(" methodargs? ")"

    methodargs: rexp -> methodargs
        | methodargs "," rexp -> methodargs_recur

    assignment: lexp [":" type] "=" rexp

    ?type: NAME

    rexp: sum               -> rexp
        | "true"            -> true
        | "false"           -> false
        | methodcall
        | logic_expr

    logic_expr: rexp "and" rexp -> _and
        | rexp "or" rexp -> _or
        | "not" rexp -> not
        | rexp "<" rexp -> lt
        | rexp ">" rexp -> gt
        | rexp "<=" rexp -> le
        | rexp ">=" rexp -> ge
        | rexp "==" rexp -> eq

    lexp: NAME              -> lexp


    ?sum: product
        | sum "+" product   -> add
        | sum "-" product   -> sub

    ?product: atom
        | product "*" atom  -> mul
        | product "/" atom  -> div

    ?atom: constant
        | "-" atom          -> neg
        | lexp              -> var_reference
        | "(" sum ")"

    ?constant: INT       -> number
        | ESCAPED_STRING    -> string


    %import common.CNAME -> NAME
    %import common.INT
    %import common.ESCAPED_STRING
    %import common.WS

    %ignore WS
"""


ch = None
# tc = None
var_dict = {}

class ASTNode:
    def __init__(self):
        self.children = []

    """Abstract base class"""
    def r_eval(self) -> List[str]:
        """Evaluate for value"""
        raise NotImplementedError(f"r_eval not implemented for node type {self.__class__.__name__}")

    def c_eval(self, true_branch: str, false_branch: str) -> List[str]:
        raise NotImplementedError(f"c_eval not implemented for node type {self.__class__.__name__}")

    def type_eval(self) -> str:
        raise NotImplementedError(f"type_eval not implemented for node type {self.__class__.__name__}")

    def pretty_label(self) -> str:
        raise NotImplementedError(f"pretty_label not implemented for node type {self.__class__.__name__}")

LAB_COUNT = 0
def new_label(prefix: str) -> str:
    global LAB_COUNT
    LAB_COUNT += 1
    return f"{prefix}_{LAB_COUNT}"




def pretty_helper(node: ASTNode, level: int, indent_str: str):
    print(node)
    # print(node.children)
    if len(node.children) == 0:
        return [indent_str*level, node.pretty_label(), '\n']

    l = [indent_str*level, node.pretty_label(), '\n']
    # print(l)
    for n in node.children:
        l += pretty_helper(n, level+1, indent_str)

    return l

def pretty_print(RootNode: ASTNode):
    print(''.join(pretty_helper(RootNode, 0, '  ')))

class SeqNode(ASTNode):
    """Sequence of statements"""
    def __init__(self, children: List[ASTNode]):
        self.children = children

    def r_eval(self) -> List[str]:
        """Evaluate for value"""
        return [child.r_eval() for child in self.children]

class RootNode(ASTNode):
    """Sequence of statements"""
    def __init__(self, program: List[ASTNode]):
        super().__init__()
        self.children.append(program)

    def r_eval(self) -> List[str]:
        """Evaluate for value"""
        program = self.children[0]
        return program.r_eval()

    def type_eval(self) -> str:
        """Evaluate for value"""
        program = self.children[0]
        return program.type_eval()

    def pretty_label(self) -> str:
        return "RootNode"


class IfNode(ASTNode):
    """if cond then block else block"""
    def __init__(self, condpart: ASTNode, thenpart: ASTNode, elsepart: ASTNode):
        super().__init__()
        self.children.append(condpart)
        self.children.append(thenpart)
        if elsepart:
            self.children.append(elsepart)

    def r_eval(self) -> List[str]:
        """Evaluate for value"""
        if len(self.children) == 2:
            condpart, thenpart = self.children
            elsepart = []
        else:
            condpart, thenpart, elsepart = self.children

        then_label = new_label("then")
        else_label = new_label("else")
        endif_label = new_label("endif")
        iftest = condpart.c_eval(then_label, else_label)
        thenblock = thenpart.r_eval()
        elseblock = elsepart.r_eval() if elsepart else []
        return (iftest
                + [then_label + ":"]
                + thenblock
                + [f"\tjump {endif_label}"]
                + [else_label + ":"]
                + elseblock
                + [endif_label + ":"])

    def type_eval(self) -> None:
        # Make sure that the condpart actually evaluates to a Boolean
        if len(self.children) == 2:
            condpart, thenpart = self.children
            thenpart.type_eval()
        else:
            global var_dict
            condpart, thenpart, elsepart = self.children

            var_dict_before_if = var_dict.copy()
            thenpart.type_eval()
            var_dict_after_then = var_dict.copy()

            var_dict = var_dict_before_if.copy()
            elsepart.type_eval()
            var_dict_after_else = var_dict.copy()
            # print(var_dict_before_if, var_dict_after_then, var_dict_after_else)

            # Construct new var_dict as a union of items. When there is an overlap assign the LCA
            new_dict = var_dict_after_then.copy()
            for var in var_dict_after_else:
                if var in new_dict:
                    new_dict[var] = ch.find_LCA(var_dict_after_else[var], new_dict[var])
                else:
                    new_dict[var] = var_dict_after_else[var]
            var_dict = new_dict


        if condpart.type_eval() != "Boolean":
            raise TypeError("If statement expects the condition to return a Boolean")


    def pretty_label(self) -> str:
        if len(self.children) == 2:
            return "IfNode"
        else:
            return "IfElseNode"



class MethodcallNode(ASTNode):
    """Method call node"""
    def __init__(self, caller: ASTNode, m_name: str, argslist: List[ASTNode]):
        super().__init__()
        self.children.append(caller)
        self.children += argslist
        self.m_name = m_name

    def r_eval(self) -> List[str]:
        #TODO: Add type here, let it be Int for now
        caller = self.children[0]
        return ([subitem for args in self.children[1:] for subitem in args.r_eval()]
                + caller.r_eval()
                + [f'\tcall Int:{self.m_name}'])

    def type_eval(self) -> str:
        caller, *argslist = self.children
        caller_type = caller.type_eval()
        args_types = [arg.type_eval() for arg in argslist]

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

    def pretty_label(self) -> str:
        return f"MethodcallNode: {self.m_name}"


class StatementNode(ASTNode):
    """Statement node"""
    def __init__(self, statement: ASTNode):
        super().__init__()
        self.children.append(statement)

    def r_eval(self) -> List[str]:
        return self.children[0].r_eval()

    def type_eval(self) -> None:
        self.children[0].type_eval()
        return None

    def pretty_label(self) -> str:
        return "StatementNode"

class StatementBlockNode(ASTNode):
    """Statement node"""
    def __init__(self, statement_block: List[ASTNode]):
        super().__init__()
        self.children = statement_block

    def r_eval(self) -> List[str]:
        return [subitem for statement in self.children for subitem in statement.r_eval()]

    def type_eval(self) -> None:
        for statement in self.children:
            statement.type_eval()
        return None

    def pretty_label(self) -> str:
        return f"StatementBlockNode: length {len(self.children)}"


class ProgramrecurNode(ASTNode):
    """Program recur Node"""
    def __init__(self, program: ASTNode, statement: ASTNode):
        super().__init__()
        self.children.append(program)
        self.children.append(statement)

    def r_eval(self) -> List[str]:
        program, statement = self.children
        return (program.r_eval()
                + statement.r_eval())

    def type_eval(self) -> None:
        program, statement = self.children
        program.type_eval()
        statement.type_eval()
        return None

    def pretty_label(self) -> str:
        return "ProgramRecurNode"


class ProgramNode(ASTNode):
    """Program  Node"""
    def __init__(self, program: ASTNode):
        super().__init__()
        self.children.append(program)

    def r_eval(self) -> List[str]:
        return (self.children[0].r_eval())

    def type_eval(self) -> None:
        self.children[0].type_eval()
        return None

    def pretty_label(self) -> str:
        return "ProgramNode"

class MethodargsrecurNode(ASTNode):
    """Methodargs recur Node"""
    def __init__(self, methodargs: ASTNode, rexp: ASTNode):
        super().__init__()
        self.children.append(methodargs)
        self.children.append(rexp)

    def r_eval(self) -> List[str]:
        methodargs, rexp = self.children
        return (methodargs.r_eval()
                + rexp.r_eval())

    def type_eval(self) -> List[str]:
        methodargs, rexp = self.children
        return (methodargs.type_eval()
                + [rexp.type_eval()])

    def pretty_label(self) -> str:
        return "MethodargsRecurNode"


class MethodargsNode(ASTNode):
    """Methodargs  Node"""
    def __init__(self, rexp: ASTNode):
        super().__init__()
        self.children.append(rexp)

    def r_eval(self) -> List[str]:
        return (self.children[0].r_eval())

    def type_eval(self) -> List[str]:
        return [self.children[0].type_eval()]

    def pretty_label(self) -> str:
        return "MethodargsNode"

class AssignmentNode(ASTNode):
    """Assignment Node"""
    def __init__(self, lexp: ASTNode, var_type: str, rexp: ASTNode):
        super().__init__()
        self.children.append(lexp)
        self.children.append(rexp)
        self.var_type = var_type

    def r_eval(self) -> List[str]:
        lexp, rexp = self.children
        return (rexp.r_eval()
                + [f'\tstore {lexp.r_eval()}'])

    def type_eval(self) -> None:

        # print('In assignment type eval')

        lexp, rexp = self.children

        actual_type = rexp.type_eval()
        declared_type = self.var_type
        prev_inferred_type = var_dict.get(lexp.value, None)
        newly_inferred_type = None

        # Add to var_dict if this is the first encounter
        if not prev_inferred_type:
            var_dict[lexp.value] = actual_type


        # If we inferred a type before ...
        if prev_inferred_type:
            new_candidate_type = ch.find_LCA(prev_inferred_type, actual_type)
            var_dict[lexp.value] = new_candidate_type
            newly_inferred_type = new_candidate_type
        else:
            newly_inferred_type = actual_type

        # If a type was declared, make sure that it is legal with the newly inferred type
        if declared_type and not ch.is_legal_assignment(declared_type, newly_inferred_type):
            raise TypeError(f'Assignment declared {declared_type} but inferred {newly_inferred_type}')

        lexp.type_eval()
        rexp.type_eval()

        return None

    def pretty_label(self) -> str:
        return f"AssignmentNode {self.var_type}"


class RexpNode(ASTNode):
    """Rexp Node"""
    def __init__(self, rexp: ASTNode):
        super().__init__()
        self.children.append(rexp)

    def r_eval(self) -> List[str]:
        return self.children[0].r_eval()

    def c_eval(self, true_branch: str, false_branch: str) -> List[str]:
        return self.children[0].c_eval(true_branch, false_branch)

    def type_eval(self) -> str:
        return self.children[0].type_eval()

    def pretty_label(self) -> str:
        return "RexpNode"


class LexpNode(ASTNode):
    """Lexp Node"""
    def __init__(self, lexp: str):
        super().__init__()
        self.value = lexp

    def r_eval(self) -> List[str]:
        return self.value

    def type_eval(self) -> None:
        return None

    def pretty_label(self) -> str:
        return f"LexpNode {self.value}"


class VarReferenceNode(ASTNode):
    """VarReferecnce Node"""
    def __init__(self, variable: ASTNode):
        super().__init__()
        self.variable = variable.r_eval()

    def r_eval(self) -> List[str]:
        return [f'\tload {self.variable}']

    #TODO: Fix mee
    def type_eval(self) -> str:
        if self.variable not in var_dict:
            raise ValueError(f'{self.variable} is referenced before assignment')
        return var_dict[self.variable]

    def pretty_label(self) -> str:
        return f'VarReferenceNode: {self.variable}'


class ConstNode(ASTNode):
    """Constant"""
    def __init__(self, value: str, value_type: str):
        super().__init__()
        self.value = value
        self.value_type = value_type

    def r_eval(self) -> List[str]:
        return [f"\tconst {self.value}"]

    def type_eval(self) -> str:
        return self.value_type

    def pretty_label(self) -> str:
        return f"ConstNode {self.value}"


class BoolNode(ASTNode):
    """Boolean """
    def __init__(self, value: str):
        super().__init__()
        self.value = value

    def r_eval(self) -> List[str]:
        return [f"\tconst {self.value}"]

    def c_eval(self, true_branch: str, false_branch: str) -> List[str]:
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
    def __init__(self, comp_op: str, left: ASTNode, right: ASTNode):
        super().__init__()
        self.comp_op = comp_op
        self.left = left
        self.right = right

    def r_eval(self) -> List[str]:
        """Called if we want a boolean VALUE rather than a branch"""
        left_code = self.left.r_eval()
        right_code = self.right.r_eval()
        return left_code + right_code + [self.comp_op]

    def c_eval(self, true_branch: str, false_branch: str) -> List[str]:
        bool_code = self.r_eval()
        return bool_code + [f"Jump if true  {true_branch}", f"Jump always {false_branch}"]

class AndNode(ASTNode):
    """Boolean and, short circuit; can be evaluated for jump or for boolean value"""
    def __init__(self, left: ASTNode, right: ASTNode):
        super().__init__()
        self.children.append(left)
        self.children.append(right)

    # FIXME: Needs r_eval to allow production of boolean value

    def r_eval(self) -> List[str]:
        left, right = self.children
        return (left.r_eval() + right.r_eval() + ['\tcall Boolean:AND'])

    def c_eval(self, true_branch: str, false_branch: str) -> List[str]:
        """Use in a conditional branch"""
        continue_label = new_label("and")
        left, right = self.children
        return (left.c_eval(continue_label, false_branch)
                + [continue_label + ":"]
                + right.c_eval(true_branch, false_branch)
                )

    def type_eval(self) -> str:
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

    def r_eval(self) -> List[str]:
        left, right = self.children
        return (left.r_eval() + right.r_eval() + ['\tcall Boolean:OR'])

    def c_eval(self, true_branch: str, false_branch: str) -> List[str]:
        """Use in a conditional branch"""
        continue_label = new_label("and")
        left, right = self.children
        return (left.c_eval(true_branch, continue_label)
                + [continue_label + ":"]
                + right.c_eval(true_branch, false_branch)
                )

    def type_eval(self) -> str:
        return "Boolean"

    def pretty_label(self) -> str:
        return "OrNode"


class Arith(ASTNode):
    """Arithmetic operations"""
    def __init__(self, op: str, left: ASTNode, right: ASTNode):
        self.op = op
        self.left = left
        self.right = right

    def r_eval(self) -> List[str]:
        return ( self.left.r_eval()
                 + self.right.r_eval()
                 + [self.op]
                 )

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

    def program_recur(self, lst) -> ASTNode:
        print(f'In program_recur {lst}')
        program, statement = lst
        return ProgramrecurNode(program, statement)

    def program(self, lst) -> ASTNode:
        print(f'In program {lst}')
        return ProgramNode(lst[0])

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
        return IfNode(condpart, thenpart, elsepart)

    def ifelseifstmt(self, lst) -> ASTNode:
        condpart, thenpart, *elifblock, elsepart = lst
        elif_node = IfNode(elifblock[-2], elifblock[-1], elsepart)

        # Number of additional elifs to handle
        num_elifs = len(elifblock) / 2 - 1
        counter = 2
        while num_elifs > 0:
            elif_node = IfNode(elifblock[-2*counter], elifblock[-2*counter + 1], elif_node)
            num_elifs -= 1
            counter += 1
        return IfNode(condpart, thenpart, elif_node)

    def _or(self, lst) -> ASTNode:
        left, right = lst
        print(f'In OR {left}, {right}')
        return OrNode(left, right)

    def _and(self, lst) -> ASTNode:
        left, right = lst
        print(f'In OR {left}, {right}')
        return AndNode(left, right)


    def type(self, lst) -> str:
        print(f'In type NAME:{lst[0]}')
        return lst[0].value

    def lexp(self, lst) -> ASTNode:
        print(f'In lexp NAME:{lst[0]}')
        return LexpNode(lst[0].value)

    def rexp(self, lst) -> ASTNode:
        print(f'In rexp NAME:{lst[0]}')
        return RexpNode(lst[0])

    # def var_reference(self, variable: str) -> Instr_dtype_pair:
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
        val = lst[0]
        print(f'In neg: {val}')
        return MethodcallNode(val, "MINUS", [ConstNode(0, 'Int')])

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

def type_check(RootNode: ASTNode) -> None:
    RootNode.type_eval()
    temp_var_dict = var_dict.copy()
    print('Variables after first pass', var_dict)
    count = 1
    while True:
        print(f'In type_check iteration number: {count}')
        RootNode.type_eval()
        print(f'Variables after pass numer: {count}', var_dict)
        count += 1
        if temp_var_dict == var_dict:
            break
    print('Finished Type Checking')

def write_to_file(RootNode: ASTNode, output_asm: str) -> None:
    instr = RootNode.r_eval()
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
    quack_parser = Lark(quack_grammar, parser='lalr')
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
    # ast.type_eval()
    print('------------------------------------------------------')
    # global tc
    # tc = TypeChecker(ch, ast)
    # print(tc.type_inference())
    type_check(ast)
    print('Printing variable dict')
    print(var_dict)
    print('------------------------------------------------------')
    write_to_file(ast, output_asm)



if __name__ == '__main__':
    if len(sys.argv) != 4:
        print('Usage: lark_parser.py [input_quack_file] [path/to/output.asm] [path/to/builtinclass.json]')
        sys.exit(1)
    main(sys.argv[1], sys.argv[2], sys.argv[3])
