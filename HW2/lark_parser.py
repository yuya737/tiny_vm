import sys
from lark import Lark, Transformer, v_args, Visitor
from lark.indenter import PythonIndenter




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

    type: NAME

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
         | lexp
         | "(" sum ")"

    %import common.CNAME -> NAME
    %import common.NUMBER
    %import common.WS

    %ignore WS
"""

@v_args(inline=True)    # Affects the signatures of the methods
class MakeAssemblyTree(Transformer):
    number = int



def main(path_to_file):
    # calc_parser = Lark(calc_grammar, parser='lalr')
    # calc = calc_parser.parse
    quack_parser = Lark(quack_grammar, parser='lalr')
    quack = quack_parser.parse
    input_str = sys.stdin.read()
    print(input_str)
    tree = MakeAssemblyTree()
    tree.transform(quack(input_str))
    print(quack(input_str).pretty())

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: lark_parser.py [path/to/output.asm]')
        sys.exit(1)
    main(sys.argv[1])
