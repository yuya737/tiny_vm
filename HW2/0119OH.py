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

python_grammar = r"""
%import python (compound_stmt, single_input, file_input, eval_input, test, suite, _NEWLINE, _INDENT, _DEDENT, COMMENT)

%extend compound_stmt: match_stmt

match_stmt: "match" test ":" cases
cases: _NEWLINE _INDENT case+ _DEDENT

case: "case" test ":" suite // test is not quite correct.

%ignore /[\t \f]+/          // WS
%ignore /\\[\t \f]*\r?\n/   // LINE_CONT
%ignore COMMENT
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

    def assign_var(self, name, value):
        self.vars[name] = value
        return value

    def var(self, name):
        try:
            return self.vars[name]
        except KeyError:
            raise Exception("Variable not found: %s" % name)




def main(path_to_file):
    # calc_parser = Lark(calc_grammar, parser='lalr')
    # calc = calc_parser.parse
    python_parser = Lark(python_grammar, parser='lalr', start=['single_input', 'file_input', 'eval_input'], postlex=PythonIndenter())
    python = python_parser.parse
    input_str = sys.stdin.read()
    print(input_str)
    tree = MakeAssemblyTree("a")
    tree.transform(python(input_str, start='file_input'))
    print(python(input_str, start='file_input').pretty())

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: lark_parser.py [path/to/output.asm]')
        sys.exit(1)
    main(sys.argv[1])
