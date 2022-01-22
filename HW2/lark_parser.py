import sys
from lark import Lark, Transformer, v_args, Visitor, Tree




calc_grammar = """
    ?start: sum
          | NAME "=" sum    -> assign_var

    ?sum: product
        | sum "+" product   -> add
        | sum "-" product   -> sub

    ?product: atom
        | product "*" atom  -> mul
        | product "/" atom  -> div

    ?atom: NUMBER           -> number
         | "-" atom         -> neg
         | NAME             -> var
         | "(" sum ")"

    %import common.CNAME -> NAME
    %import common.NUMBER
    %import common.WS_INLINE

    %ignore WS_INLINE
"""

quack_grammar = """
    ?start: program

    program: statement
        | program statement

    statement: rexp ";"
        | assignment ";"
        | methodcall ";"

    methodcall: rexp "." NAME "(" ")"

    assignment: lexp ":" type "=" rexp

    ?type: NAME

    rexp: sum

    lexp: NAME

    ?sum: product
        | sum "+" product   -> add
        | sum "-" product   -> sub

    ?product: atom
        | product "*" atom  -> mul
        | product "/" atom  -> div

    ?atom: NUMBER           -> number
         | "-" atom         -> neg
         | lexp             -> var_reference
         | "(" sum ")"

    %import common.CNAME -> NAME
    %import common.NUMBER
    %import common.WS

    %ignore WS
"""

# Test if a children is a instruction or not
def is_instr(val):
    return isinstance(val, list)

# class MakeAssemblyTree(Transformer):
@v_args(inline=True)    # Affects the signatures of the methods
class MakeAssemblyTree(Transformer):
    number = int


    def __init__(self, file):
        self.vars = {}
        self.file = file
        self.cur_ops = []

    def write_to_file(self):
        for line in self.cur_ops:
            # self.file.write(line)
            print(line, end="")

    def methodcall(self, a, b):
        print(f'In method call rexp:{a}, NAME:{b}')

    def assignment(self, a, b, c):
        temp_ops = []
        if is_instr(c):
            temp_ops += c
        else:
            temp_ops.append(f'\tconst {c}\n')
            temp_ops.append(f'\tstore {a}\n')
        self.cur_ops = temp_ops
        print(f'In assignment lexp:{a}, type:{b}, rexp:{c}')
        return temp_ops


    def type(self, a):
        print(f'In type NAME:{a}')
        return f'{a}'

    def lexp(self, a):
        print(f'In lexp NAME:{a}')
        return f'{a}'

    def rexp(self, a):
        print(f'In rexp NAME:{a}')
        return f'{a}'

    def var_reference(self, a):
        temp_ops = self.cur_ops
        temp_ops.append('\tload $\n')
        temp_ops.append(f'\tload {a}\n')
        print(f'In var_reference var:{a}')
        return temp_ops

    def neg(self, a):
        temp_ops = []
        if is_instr(a):
            temp_ops += a
            temp_ops.append('\tconst 0\n')
            temp_ops.append('\tcall Int:minus\n')
        else:
            temp_ops.append(f'\tconst {a}\n')
            temp_ops.append('\tconst 0\n')
            temp_ops.append('\tcall Int:minus\n')
        self.cur_ops = temp_ops
        print(f'Negating {a}')
        return temp_ops


    def add(self, a,b):
        temp_ops = []
        if is_instr(a) and is_instr(b):
            temp_ops += a
            temp_ops += b
            temp_ops.append('\tcall Int:plus\n')
        elif is_instr(a):
            temp_ops += a
            temp_ops.append(f'\tconst {b}\n')
            temp_ops.append('\tcall Int:plus\n')
        elif is_instr(b):
            temp_ops += b
            temp_ops.append(f'\tconst {a}\n')
            temp_ops.append('\tcall Int:plus\n')
        else:
            temp_ops.append(f'\tconst {a}\n')
            temp_ops.append(f'\tconst {b}\n')
            temp_ops.append('\tcall Int:plus\n')
        self.cur_ops = temp_ops
        print(f'Adding {a}, {b}')
        return temp_ops

    def sub(self, a,b):
        temp_ops = []
        if is_instr(a) and is_instr(b):
            temp_ops += b
            temp_ops += a
            temp_ops.append('\tcall Int:minus\n')
        elif is_instr(a):
            temp_ops.insert(0, f'\tconst {b}\n')
            temp_ops += a
            temp_ops.append('\tcall Int:minus\n')
        elif is_instr(b):
            temp_ops += b
            temp_ops.append(f'\tconst {a}\n')
            temp_ops.append('\tcall Int:minus\n')
        else:
            temp_ops.append(f'\tconst {b}\n')
            temp_ops.append(f'\tconst {a}\n')
            temp_ops.append('\tcall Int:minus\n')
        self.cur_ops = temp_ops
        print(f'Subtracting {a}, {b}')
        return temp_ops

    def mul(self, a,b):
        temp_ops = []
        if is_instr(a) and is_instr(b):
            temp_ops += a
            temp_ops += b
            temp_ops.append('\tcall Int:times\n')
        elif is_instr(a):
            temp_ops += a
            temp_ops.append(f'\tconst {b}\n')
            temp_ops.append('\tcall Int:times\n')
        elif is_instr(b):
            temp_ops += b
            temp_ops.append(f'\tconst {a}\n')
            temp_ops.append('\tcall Int:times\n')
        else:
            temp_ops.append(f'\tconst {a}\n')
            temp_ops.append(f'\tconst {b}\n')
            temp_ops.append('\tcall Int:times\n')
        self.cur_ops = temp_ops
        print(f'Multiplying {a}, {b}')
        return temp_ops

    def div(self, a,b):
        temp_ops = []
        if is_instr(a) and is_instr(b):
            temp_ops += b
            temp_ops += a
            temp_ops.append('\tcall Int:divide\n')
        elif is_instr(a):
            temp_ops.insert(0, f'\tconst {b}\n')
            temp_ops += a
            temp_ops.append('\tcall Int:divide\n')
        elif is_instr(b):
            temp_ops += b
            temp_ops.append(f'\tconst {a}\n')
            temp_ops.append('\tcall Int:divide\n')
        else:
            temp_ops.append(f'\tconst {b}\n')
            temp_ops.append(f'\tconst {a}\n')
            temp_ops.append('\tcall Int:divide\n')
        self.cur_ops = temp_ops
        print(f'Dividing {a}, {b}')
        return temp_ops

    def assign_var(self, name, value):
        self.vars[name] = value
        return value

    def var(self, name):
        try:
            return self.vars[name]
        except KeyError:
            raise Exception("Variable not found: %s" % name)

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
    # calc_parser = Lark(calc_grammar, parser='lalr')
    # calc = calc_parser.parse
    quack_parser = Lark(quack_grammar, parser='lalr')
    quack = quack_parser.parse
    with open(quack_file) as f:
        input_str = f.read()
    print(input_str)
    tree = MakeAssemblyTree('out.asm')
    print('---------------------------')
    POT(quack(input_str))
    print('---------------------------')
    tree.transform(quack(input_str))
    print('---------------------------')
    print(quack(input_str).pretty())
    print('---------------------------')
    tree.write_to_file()

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: lark_parser.py [input_quack_file] [path/to/output.asm]')
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
