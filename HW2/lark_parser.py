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
class instr_dtype_pair:
    instr: List[str]
    dtype: str

# Keep track of the input and ouptut dtypes for each function
@dataclass
class input_output_dtypes:
    input_dtype: List[str]
    output_dtype: str

# class MakeAssemblyTree(Transformer):
@v_args(inline=True)    # Affects the signatures of the methods
class MakeAssemblyTree(Transformer):

    def __init__(self, file):
        self.vars = {}
        self.file = file
        self.var_dict = {}
        self.input_output_dtypes_dict = {}
        self.final_instr = []

        # Functions to populate input_output_dtypes:
        # neg, add, sub, mul, div
        self.input_output_dtypes_dict['neg'] = [input_output_dtypes(['Int'], 'Int')]
        self.input_output_dtypes_dict['add'] = [input_output_dtypes(['Int', 'Int'], 'Int'),
                                                input_output_dtypes(['String', 'String'], 'String')]
        self.input_output_dtypes_dict['sub'] = [input_output_dtypes(['Int', 'Int'], 'Int')]
        self.input_output_dtypes_dict['mul'] = [input_output_dtypes(['Int', 'Int'], 'Int')]
        self.input_output_dtypes_dict['div'] = [input_output_dtypes(['Int', 'Int'], 'Int')]

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


    def root(self, final_instr: List[instr_dtype_pair]) -> None:
        self.final_instr = final_instr.instr


    def number(self, num: Token) -> instr_dtype_pair:
        return instr_dtype_pair([f'\tconst {num}\n'], 'Int')

    def string(self, string: Token) -> instr_dtype_pair:
        return instr_dtype_pair([f'\tconst {string}\n'], 'String')

    def true(self) -> instr_dtype_pair:
        return instr_dtype_pair([f'\tconst true\n'], 'Boolean')

    def false(self) -> instr_dtype_pair:
        return instr_dtype_pair([f'\tconst falst\n'], 'Boolean')


    def methodcall(self, rexp: instr_dtype_pair , name: str) -> instr_dtype_pair:
        print(f'In method call rexp:{rexp}, NAME:{name}')
        temp_ops = rexp.instr
        temp_ops.append(f'\tcall {rexp.dtype}:{name}\n')
        return instr_dtype_pair(temp_ops, 'None')

    def statement(self, expression: instr_dtype_pair) -> instr_dtype_pair:
        print(f'In statement {expression.instr}')
        return instr_dtype_pair(expression.instr, 'None')

    def program_recur(self, expression_1: instr_dtype_pair, expression_2: instr_dtype_pair) -> instr_dtype_pair:
        print(f'In program_recur expression_1:{expression_1.instr} expression_2:{expression_2.instr}')
        return instr_dtype_pair(expression_1.instr + expression_2.instr, 'None')

    def program(self, expression: instr_dtype_pair) -> instr_dtype_pair:
        print(f'In program expression:{expression.instr}')
        return instr_dtype_pair(expression.instr, 'None')


    def assignment(self, lexp: instr_dtype_pair, type: Token, rexp: instr_dtype_pair) -> instr_dtype_pair:
        temp_ops = rexp.instr
        temp_ops += [f'\tstore {lexp}\n']

        # Save variable assignment to allocate memory via .local
        self.var_dict[lexp.value] = type.value

        print(f'In assignment lexp:{lexp}, type:{type}, rexp:{rexp}')
        return instr_dtype_pair(temp_ops, 'None')

    def type(self, a: str) -> str:
        print(f'In type NAME:{a}')
        return f'{a}'

    def lexp(self, a: instr_dtype_pair) -> instr_dtype_pair:
        print(f'In lexp NAME:{a}')
        return a

    def rexp(self, a: instr_dtype_pair) -> instr_dtype_pair:
        print(f'In rexp NAME:{a}')
        return a

    def var_reference(self, variable: str) -> instr_dtype_pair:
        if variable not in self.var_dict:
            raise ValueError(f'{variable} referenced before assignment')
        else:
            temp_ops = [f'\tload {variable}\n']
            print(f'In var_reference var:{variable}')
            return instr_dtype_pair(temp_ops, self.var_dict[variable])

    # Check if the current function arguments are valid. If so, return receiver type and return type
    def check_if_valid_func_invocation(self, func_name: str, input_type_list: List[str]):
        for candidate in self.input_output_dtypes_dict[func_name]:
            # If matching one exists return it
            if input_type_list == candidate.input_dtype:
                return (True, candidate.input_dtype[0], candidate.output_dtype)

        return (False, None, None)




    def neg(self, expression: instr_dtype_pair) -> instr_dtype_pair:
        input_type_list = [expression.dtype]
        valid_invocation, receiver_type, return_type = self.check_if_valid_func_invocation('neg', input_type_list)
        if valid_invocation:
            temp_ops = expression.instr
            temp_ops += ['\tconst 0\n']
            temp_ops.append(f'\tcall {receiver_type}:minus\n')
            print(f'Negating {expression.instr}')
            return instr_dtype_pair(temp_ops, return_type)
        else:
            raise ValueError('Type check failed in neg')


    def add(self, expression_1: instr_dtype_pair, expression_2: instr_dtype_pair) -> instr_dtype_pair:
        input_type_list = [expression_1.dtype, expression_2.dtype]
        print(input_type_list)
        valid_invocation, receiver_type, return_type = self.check_if_valid_func_invocation('add', input_type_list)
        if valid_invocation:
            temp_ops = expression_2.instr
            temp_ops += expression_1.instr
            temp_ops.append(f'\tcall {receiver_type}:plus\n')
            print(f'Adding {expression_1.instr}, {expression_2.instr}')
            return instr_dtype_pair(temp_ops, return_type)
        else:
            raise ValueError('Type check failed in add')

    def sub(self, expression_1: instr_dtype_pair, expression_2: instr_dtype_pair) -> instr_dtype_pair:
        input_type_list = [expression_1.dtype, expression_2.dtype]
        valid_invocation, receiver_type, return_type = self.check_if_valid_func_invocation('sub', input_type_list)
        if valid_invocation:
            temp_ops = expression_2.instr
            temp_ops += expression_1.instr
            temp_ops.append(f'\tcall {receiver_type}:minus\n')
            print(f'Substracting {expression_1.instr}, {expression_2.instr}')
            return instr_dtype_pair(temp_ops, return_type)
        else:
            raise ValueError('Type check failed in sub')

    def mul(self, expression_1: instr_dtype_pair, expression_2: instr_dtype_pair) -> instr_dtype_pair:
        input_type_list = [expression_1.dtype, expression_2.dtype]
        valid_invocation, receiver_type, return_type = self.check_if_valid_func_invocation('mul', input_type_list)
        if valid_invocation:
            temp_ops = expression_2.instr
            temp_ops += expression_1.instr
            temp_ops.append(f'\tcall {receiver_type}:times\n')
            print(f'Multiplying {expression_1.instr}, {expression_2.instr}')
            return instr_dtype_pair(temp_ops, return_type)
        else:
            raise ValueError('Type check failed in mul')

    def div(self, expression_1: instr_dtype_pair, expression_2: instr_dtype_pair) -> instr_dtype_pair:
        input_type_list = [expression_1.dtype, expression_2.dtype]
        valid_invocation, receiver_type, return_type = self.check_if_valid_func_invocation('div', input_type_list)
        if valid_invocation:
            temp_ops = expression_2.instr
            temp_ops += expression_1.instr
            temp_ops.append(f'\tcall {receiver_type}:divide\n')
            print(f'Diving {expression_1.instr}, {expression_2.instr}')
            return instr_dtype_pair(temp_ops, return_type)
        else:
            raise ValueError('Type check failed in div')

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
    tree.transform(quack(input_str))
    print('---------------------------')
    tree.write_to_file()

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: lark_parser.py [input_quack_file] [path/to/output.asm]')
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
