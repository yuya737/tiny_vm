import sys
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type, Union
from lark import Lark, Transformer, v_args, Visitor, Tree, Token
from dataclasses import dataclass

quack_grammar = """
    ?start: program -> root

    program: statement -> program
        | program statement -> program_recur

    statement: rexp ";"
        | assignment ";"

    methodcall: rexp "." NAME "(" ")"

    assignment: lexp ":" type "=" rexp

    ?type: NAME

    rexp: sum               -> rexp
        | "true"            -> true
        | "false"           -> false
        | methodcall

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

# Keep track of each instruction and the data type of that set of instructions
@dataclass
class Instr_dtype_pair:
    instr: List[str]
    dtype: str

# Keep track of the input and ouptut dtypes for each function
@dataclass
class Input_output_dtypes:
    input_dtype: List[str]
    output_dtype: str


class ASTNode:
    """Abstract base class"""
    def r_eval(self) -> List[str]:
        """Evaluate for value"""
        raise NotImplementedError(f"r_eval not implemented for node type {self.__class__.__name__}")

    def c_eval(self, true_branch: str, false_branch: str) -> List[str]:
        raise NotImplementedError(f"c_eval not implemented for node type {self.__class__.__name__}")

    def pretty_label(self) -> str:
        raise NotImplementedError(f"pretty_label not implemented for node type {self.__class__.__name__}")

def pretty_helper(Node: ASTNode, level: int, indent_str: str):
    print(Node)
    if Node.is_leaf():
        return [indent_str*level, Node.pretty_label(), '\n']

    l = [indent_str*level, Node.pretty_label(), '\n']
    # print(l)
    for n in vars(Node).values():
        l += pretty_helper(n, level+1, indent_str)

    return l

def pretty_print(RootNode: ASTNode):
    print(''.join(pretty_helper(RootNode, 0, '   ')))

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
        self.program = program

    def r_eval(self) -> List[str]:
        """Evaluate for value"""
        return self.program.r_exp()

    def pretty_label(self) -> str:
        return "RootNode"

    def is_leaf(self) -> bool:
        return False



class IfNode(ASTNode):
    """if cond then block else block"""
    def __init__(self, condpart: ASTNode, thenpart: ASTNode, elsepart: ASTNode):
        self.condpart = condpart
        self.thenpart = thenpart
        self.elsepart = elsepart

    def r_eval(self) -> List[str]:
        """Evaluate for value"""
        then_label = new_label("then")
        else_label = new_label("else")
        endif_label = new_label("endif")
        iftest = self.condpart.c_eval(then_label, else_label)
        thenblock = self.thenpart.r_eval()
        elseblock = self.elsepart.r_eval()
        return (iftest
                + [then_label + ":"]
                + thenblock
                + [f"Jump always {endif_label}"]
                + [else_label + ":"]
                + elseblock
                + [endif_label + ":"])

    def pretty_label(self) -> str:
        return "IfNode"

    def is_leaf(self) -> bool:
        return False

class MethodArgumentNode(ASTNode):
    def __init__(self, argslist: List[ASTNode]):
        self.argslist = argslist

    def r_eval(self) ->



class MethodcallNode(ASTNode):
    """Method call node"""
    def __init__(self, caller: ASTNode, m_name: ASTNode, argslist: List[ASTNode]):
        self.caller = caller
        self.m_name = m_name
        self.argslist = argslist

    def r_eval(self) -> List[str]:
        #TODO: Add type here, let it be Int for now
        return ([args.r_exp() for args in self.argslist]
                + self.caller.r_exp
                + [f'\tcall Int:{self.m_name}'])

    def pretty_label(self) -> str:
        return "MethodcallNode"

    def is_leaf(self) -> bool:
        return False

class StatementNode(ASTNode):
    """Statement node"""
    def __init__(self, statement: ASTNode):
        self.statement = statement

    def r_eval(self) -> List[str]:
        return self.statement.r_exp()

    def pretty_label(self) -> str:
        return "StatementNode"

    def is_leaf(self) -> bool:
        return False

class ProgramrecurNode(ASTNode):
    """Program recur Node"""
    def __init__(self, program: ASTNode, statement: ASTNode):
        self.program = program
        self.statement = statement

    def r_eval(self) -> List[str]:
        return (self.program.r_exp()
                + self.statement.r_exp())

    def pretty_label(self) -> str:
        return "ProgramRecurNode"

    def is_leaf(self) -> bool:
        return False

class ProgramNode(ASTNode):
    """Program  Node"""
    def __init__(self, program: ASTNode):
        self.program = program

    def r_eval(self) -> List[str]:
        return (self.program.r_exp())

    def pretty_label(self) -> str:
        return "ProgramNode"

    def is_leaf(self) -> bool:
        return False

class AssignmentNode(ASTNode):
    """Assignment Node"""
    def __init__(self, lexp: ASTNode, rexp: ASTNode):
        self.lexp = lexp
        self.rexp = rexp

    def r_eval(self) -> List[str]:
        return (self.rexp.r_eval()
                + [f'\tstore {self.lexp.r_eval()}'])

    def pretty_label(self) -> str:
        return "AssignmentNode"

    def is_leaf(self) -> bool:
        return False

class RexpNode(ASTNode):
    """Rexp Node"""
    def __init__(self, rexp: ASTNode):
        self.rexp = rexp

    def r_eval(self) -> List[str]:
        return self.rexp.r_eval()

    def pretty_label(self) -> str:
        return "RexpNode"

    def is_leaf(self) -> bool:
        return False

class LexpNode(ASTNode):
    """Lexp Node"""
    def __init__(self, lexp: ASTNode):
        self.lexp = lexp

    def r_eval(self) -> List[str]:
        return self.lexp.r_eval()

    def pretty_label(self) -> str:
        return f"LexpNode {self.lexp}"

    def is_leaf(self) -> bool:
        return True

class VarReferenceNode(ASTNode):
    """VarReferecnce Node"""
    def __init__(self, variable: str):
        self.variable = variable

    def r_eval(self) -> List[str]:
        return [f'\tload {self.variable}']

    def pretty_label(self) -> str:
        return f"VarReferenceNode"

    def is_leaf(self) -> bool:
        return False

class ConstNode(ASTNode):
    """Constant"""
    def __init__(self, value: str):
        self.value = value

    def r_eval(self) -> List[str]:
        return [f"const {self.value}"]

    def pretty_label(self) -> str:
        return f"ConstNode {self.value}"

    def is_leaf(self) -> bool:
        return True

class TypeNode(ASTNode):
    """Type"""
    def __init__(self, type: str):
        self.type = type

    def r_eval(self) -> List[str]:
        return [f"const {self.type}"]

    def pretty_label(self) -> str:
        return f"TypeNode {self.type}"

    def is_leaf(self) -> bool:
        return True

class MNameNode(ASTNode):
    """Method Name"""
    def __init__(self, m_name: str):
        self.m_name = m_name

    def r_eval(self) -> List[str]:
        return [f"const {self.m_name}"]

    def pretty_label(self) -> str:
        return f"m_nameNode {self.m_name}"

    def is_leaf(self) -> bool:
        return True

class BoolNode(ASTNode):
    """Boolean """
    def __init__(self, value: str):
        self.value = value

    def r_eval(self) -> List[str]:
        return [f"const {self.value}"]

    def pretty_label(self) -> str:
        return f"BoolNode {self.value}"

    def is_leaf(self) -> bool:
        return True


class ComparisonNode(ASTNode):
    """Comparisons are the leaves of conditional branches
    and can also return boolean values
    """
    def __init__(self, comp_op: str, left: ASTNode, right: ASTNode):
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
        self.left = left
        self.right = right

    # FIXME: Needs r_eval to allow production of boolean value

    def c_eval(self, true_branch: str, false_branch: str) -> List[str]:
        """Use in a conditional branch"""
        continue_label = new_label("and")
        return ( self.left.c_eval(continue_label, false_branch)
                + [continue_label + ":"]
                + self.right.c_eval(true_branch, false_branch)
                 )


class OrNode(ASTNode):
    """Boolean or, short circuit; can be evaluated for jump or for boolean value"""

    def __init__(self, left: ASTNode, right: ASTNode):
        self.left = left
        self.right = right

    # FIXME: Needs r_eval to allow production of boolean value

    def c_eval(self, true_branch: str, false_branch: str) -> List[str]:
        """Use in a conditional branch"""
        continue_label = new_label("and")
        return (self.left.c_eval(true_branch, continue_label)
                + [continue_label + ":"]
                + self.right.c_eval(true_branch, false_branch)
                )


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
        self.Input_output_dtypes_dict['neg'] = [Input_output_dtypes(['Int'], 'Int')]
        self.Input_output_dtypes_dict['add'] = [Input_output_dtypes(['Int', 'Int'], 'Int'),
                                                Input_output_dtypes(['String', 'String'], 'String')]
        self.Input_output_dtypes_dict['sub'] = [Input_output_dtypes(['Int', 'Int'], 'Int')]
        self.Input_output_dtypes_dict['mul'] = [Input_output_dtypes(['Int', 'Int'], 'Int')]
        self.Input_output_dtypes_dict['div'] = [Input_output_dtypes(['Int', 'Int'], 'Int')]

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

    # def number(self, num: Token) -> Instr_dtype_pair:
    def number(self, lst) -> ASTNode:
        print(f'In number {lst}')
        return ConstNode(int(lst[0]))

    # def string(self, string: Token) -> Instr_dtype_pair:
    def string(self, lst) -> ASTNode:
        print(f'In string {lst}')
        return ConstNode(str(lst[0]))

    # def true(self) -> Instr_dtype_pair:
    def true(self, lst) -> ASTNode:
        print(f'In true {lst}')
        return BoolNode(str(lst[0]))

    # def false(self) -> Instr_dtype_pair:
    def false(self, lst) -> ASTNode:
        print(f'In true {lst}')
        return BoolNode(str(lst[0]))

    # def methodcall(self, rexp: Instr_dtype_pair , name: str) -> Instr_dtype_pair:
    def methodcall(self, lst) -> ASTNode:
        print(f'In methodcall {lst}')
        caller, m_name = lst
        return MethodcallNode(caller, MNameNode(m_name))

    # def statement(self, expression: Instr_dtype_pair) -> Instr_dtype_pair:
    def statement(self, lst) -> ASTNode:
        print(f'In statement {lst}')
        return StatementNode(lst[0])

    # def program_recur(self, expression_1: Instr_dtype_pair, expression_2: Instr_dtype_pair) -> Instr_dtype_pair:
    def program_recur(self, lst) -> ASTNode:
        print(f'In program_recur {lst}')
        program, statement = lst
        return ProgramrecurNode(program, statement)

    # def program(self, expression: Instr_dtype_pair) -> Instr_dtype_pair:
    def program(self, lst) -> ASTNode:
        print(f'In program {lst}')
        return ProgramNode(lst[0])

    # def assignment(self, lexp: Instr_dtype_pair, type: Token, rexp: Instr_dtype_pair) -> Instr_dtype_pair:
    def assignment(self, lst) -> ASTNode:
        lexp, type, rexp = lst

        print(f'In assignment lexp:{lexp}, type:{type}, rexp:{rexp}')
        return AssignmentNode(lexp, rexp)


    def type(self, lst) -> str:
        print(f'In type NAME:{lst[0]}')
        return TypeNode(lst[0].value)

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
        return MethodcallNode(val, MNameNode("minus"), [ConstNode(0)])


    # def add(self, expression_1: Instr_dtype_pair, expression_2: Instr_dtype_pair) -> Instr_dtype_pair:
    def add(self, lst) -> ASTNode:
        val1, val2 = lst
        print(f'In add: {val1}, {val2}')
        return MethodcallNode(val1, MNameNode("add"), [ConstNode(val2)])

    def sub(self, lst) -> ASTNode:
        val1, val2 = lst
        print(f'In sub: {val1}, {val2}')
        return MethodcallNode(val1, MNameNode("minus"), [ConstNode(val2)])

    def mul(self, lst) -> ASTNode:
        val1, val2 = lst
        print(f'In mul: {val1}, {val2}')
        return MethodcallNode(val1, MNameNode("times"), [ConstNode(val2)])

    def div(self, lst) -> ASTNode:
        val1, val2 = lst
        print(f'In mul: {val1}, {val2}')
        return MethodcallNode(val1, MNameNode("divide"), [ConstNode(val2)])

def POT(Node):
    if isinstance(Node, Tree):
        for child in Node.children:
            POT(child)
        # breakpoint()
        print('Tree', Node.data, Node.children)
    else:
        # Is a token
        print('Token', Node.type, Node.value)


def main(quack_file, output_asm):
    quack_parser = Lark(quack_grammar, parser='lalr')
    quack = quack_parser.parse
    with open(quack_file) as f:
        input_str = f.read()
    print(input_str)
    tree = MakeAssemblyTree(output_asm)
    print('---------------------------')
    print(quack(input_str).pretty())
    print('---------------------------')
    ast = tree.transform(quack(input_str))
    print('---------------------------')
    print('Printing Transformed AST')
    breakpoint()
    pretty_print(ast)

    # tree.write_to_file()

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: lark_parser.py [input_quack_file] [path/to/output.asm]')
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
