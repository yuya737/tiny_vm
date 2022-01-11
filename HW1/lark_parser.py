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


@v_args(inline=True)    # Affects the signatures of the methods
# class MakeAssemblyTree(Visitor):
class MakeAssemblyTree(Transformer):
    # from operator import add, sub, mul, truediv as div, neg
    from operator import neg
    number = int

    def __init__(self, file):
        self.vars = {}
        self.file = file

    def add(self, a,b):
        if a is None and b is None:
            self.file.write('\tcall Int:plus\n')
        elif a is None:
            self.file.write(f'\tconst {b}\n')
            self.file.write('\tcall Int:plus\n')
        elif b is None:
            self.file.write(f'\tconst {a}\n')
            self.file.write('\tcall Int:plus\n')
        else:
            self.file.write(f'\tconst {a}\n')
            self.file.write(f'\tconst {b}\n')
            self.file.write('\tcall Int:plus\n')
        print(f'Adding {a}, {b}')
    def sub(self, a,b):
        if a is None and b is None:
            self.file.write('\tcall Int:minus\n')
        elif a is None:
            self.file.write(f'\tconst {b}\n')
            self.file.write('\tcall Int:minus\n')
        elif b is None:
            self.file.write(f'\tconst {a}\n')
            self.file.write('\tcall Int:minus\n')
        else:
            self.file.write(f'\tconst {a}\n')
            self.file.write(f'\tconst {b}\n')
            self.file.write('\tcall Int:minus\n')
        print(f'Subtracting {a}, {b}')
    def mul(self, a,b):
        if a is None and b is None:
            self.file.write('\tcall Int:times\n')
        elif a is None:
            self.file.write(f'\tconst {b}\n')
            self.file.write('\tcall Int:times\n')
        elif b is None:
            self.file.write(f'\tconst {a}\n')
            self.file.write('\tcall Int:times\n')
        else:
            self.file.write(f'\tconst {a}\n')
            self.file.write(f'\tconst {b}\n')
            self.file.write('\tcall Int:times\n')
        print(f'Multiplying {a}, {b}')
    def div(self, a,b):
        if a is None and b is None:
            self.file.write('\tcall Int:divide\n')
        elif a is None:
            self.file.write(f'\tconst {b}\n')
            self.file.write('\tcall Int:divide\n')
        elif b is None:
            self.file.write(f'\tconst {a}\n')
            self.file.write('\tcall Int:divide\n')
        else:
            self.file.write(f'\tconst {a}\n')
            self.file.write(f'\tconst {b}\n')
            self.file.write('\tcall Int:divide\n')
        print(f'Dividing {a}, {b}')

    def assign_var(self, name, value):
        self.vars[name] = value
        return value

    def var(self, name):
        try:
            return self.vars[name]
        except KeyError:
            raise Exception("Variable not found: %s" % name)


# calc_parser = Lark(calc_grammar, parser='lalr', transformer=CalculateTree())
calc_parser = Lark(calc_grammar, parser='lalr')
calc = calc_parser.parse


def main(path_to_file):
    while True:
        try:
            s = input('> ')
        except EOFError:
            break
        with open(path_to_file, 'w') as file:
            file.write('.class Sample:Obj\n')
            file.write('\n')
            file.write('.method $constructor\n')
            # breakpoint()
            # MakeAssemblyTree(file).transform(calc(s))
            MakeAssemblyTree(file).visit(calc(s))
            print(calc(s))
            print(calc(s).pretty())
            file.write('\tcall Int:print\n')
            file.write('\tpop\n')
            file.write('\thalt\n')
            file.close()


def test():
    print(calc("a = 1+2"))
    print(calc("1+a*-3"))


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: lark_parser.py [path/to/output.asm]')
        sys.exit(1)
    # test()
    main(sys.argv[1])
