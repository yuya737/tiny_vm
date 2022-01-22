import sys
from lark import Lark, Transformer, v_args, Visitor


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

# Test if a children is a instruction or not
def is_instr(val):
    return isinstance(val, list)


@v_args(inline=True)    # Affects the signatures of the methods
class MakeAssemblyTree(Transformer):
    number = int


    def __init__(self, file):
        self.vars = {}
        self.file = file
        self.cur_ops = []

    def write_to_file(self):
        for line in self.cur_ops:
            self.file.write(line)

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




def main(path_to_file):
    calc_parser = Lark(calc_grammar, parser='lalr')
    calc = calc_parser.parse
    while True:
        try:
            s = input('> ')
        except EOFError:
            break
        with open(path_to_file, 'w') as file:
            file.write('.class Sample:Obj\n')
            file.write('\n')
            file.write('.method $constructor\n')
            tree = MakeAssemblyTree(file)
            tree.transform(calc(s))
            breakpoint()
            tree.write_to_file()
            print(calc(s).pretty())
            file.write('\tcall Int:print\n')
            file.write('\tpop\n')
            file.write('\thalt\n')
            file.close()

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: lark_parser.py [path/to/output.asm]')
        sys.exit(1)
    main(sys.argv[1])
