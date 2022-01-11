"""
Basic calculator
================

A simple example of a REPL calculator

This example shows how to write a basic calculator with variables.
"""
from lark import Lark, Transformer, v_args



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
class MakeAssemblyTree(Transformer):
    # from operator import add, sub, mul, truediv as div, neg
    from operator import neg
    number = float

    def __init__(self, file):
        self.vars = {}
        self.file = file

    def add(self, a,b):
        print(f'Adding {a}, {b}')
        self.file.write(f'Adding {a}, {b}')
    def sub(self, a,b):
        print(f'Subtracting {a}, {b}')
    def mul(self, a,b):
        print(f'Multiplying {a}, {b}')
    def div(self, a,b):
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


def main():
    while True:
        try:
            s = input('> ')
        except EOFError:
            break
        with open('text.asm', 'w') as file:
            breakpoint()
            MakeAssemblyTree(file).transform(calc(s))
            print(calc(s))
            print(calc(s).pretty())


def test():
    print(calc("a = 1+2"))
    print(calc("1+a*-3"))


if __name__ == '__main__':
    # test()
    main()
