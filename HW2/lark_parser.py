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
    ?start: program -> root

    program: statement -> program
        | program statement -> program_recur

    statement: rexp ";"
        | assignment ";"
        | methodcall ";"

    methodcall: rexp "." NAME "(" ")"

    assignment: lexp ":" type "=" rexp

    ?type: NAME

    rexp: sum               -> rexp
         | ESCAPED_STRING  -> string

    lexp: NAME              -> lexp

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
    %import common.ESCAPED_STRING
    %import common.WS

    %ignore WS
"""

# Test if a children is a instruction or not
def is_instr(val):
    return isinstance(val, list)

# class MakeAssemblyTree(Transformer):
@v_args(inline=True)    # Affects the signatures of the methods
class MakeAssemblyTree(Transformer):

    def __init__(self, file):
        self.vars = {}
        self.file = file
        self.var_dict = {}

    def number(self, a):
        return ([f'\tconst {a}\n'], 'Int')

    def string(self, a):
        return ([f'\tconst {a}\n'], 'String')

    def root(self, a):
        with open(self.file, 'w') as file:
            print(self.var_dict)
            file.write('.class Main:Obj\n')
            file.write('\n')
            file.write('.method $constructor\n')
            file.write(f'.local {",".join(self.var_dict.keys())}\n')
            for line in a:
                file.write(line)
            file.write('\tpop\n')
            file.write('\thalt\n')

    def methodcall(self, a, b):
        print(f'In method call rexp:{a}, NAME:{b}')
        temp_ops = a[0]
        temp_ops.append(f'\tcall {a[1]}:{b}\n')
        return temp_ops

    def statement(self, a):
        print(f'In statement {a}')
        return a

    def program_recur(self, a ,b):
        print(f'In program_recur a:{a} b:{b}')
        return a+b

    def program(self, a):
        print(f'In program a:{a}')
        return a


    def assignment(self, a, b, c):
        temp_ops = []
        temp_ops += c[0]
        temp_ops += [f'\tstore {a}\n']
        self.var_dict[a.value] = b.value
        print(f'In assignment lexp:{a}, type:{b}, rexp:{c}')
        return temp_ops


    def type(self, a):
        print(f'In type NAME:{a}')
        return f'{a}'

    def lexp(self, a):
        print(f'In lexp NAME:{a}')
        return a

    def rexp(self, a):
        print(f'In rexp NAME:{a}')
        return a

    def var_reference(self, a):
        if a not in self.var_dict:
            raise ValueError(f'{a} referenced before assignment')
        else:
            temp_ops = [f'\tload {a}\n']
            print(f'In var_reference var:{a}')
            return (temp_ops, self.var_dict[a])

    def neg(self, a):
        if a[1] == 'Int' and b[1] == 'Int':
            temp_ops = a
            temp_ops += ['\tconst 0\n']
            temp_ops.append('\tcall Int:minus\n')
            print(f'Negating {a}')
            return (temp_ops, 'Int')
        else:
            raise ValueError('Type check failed in neg')


    def add(self, a,b):
        if a[1] == 'Int' and b[1] == 'Int':
            temp_ops = a[0]
            temp_ops += b[0]
            temp_ops.append('\tcall Int:plus\n')
            print(f'Adding {a}, {b}')
            return (temp_ops, 'Int')
        else:
            raise ValueError('Type check failed in add')

    def sub(self, a,b):
        if a[1] == 'Int' and b[1] == 'Int':
            temp_ops = b[0]
            temp_ops += a[0]
            temp_ops.append('\tcall Int:minus\n')
            return (temp_ops, 'Int')
        else:
            raise ValueError('Type check failed in sub')

    def mul(self, a,b):
        if a[1] == 'Int' and b[1] == 'Int':
            temp_ops = a[0]
            temp_ops += b[0]
            temp_ops.append('\tcall Int:times\n')
            print(f'Multiplying {a}, {b}')
            return (temp_ops, 'Int')
        else:
            raise ValueError('Type check failed in mul')

    def div(self, a,b):
        if a[1] == 'Int' and b[1] == 'Int':
            temp_ops = b[0]
            temp_ops += a[0]
            temp_ops.append('\tcall Int:divide\n')
            print(f'Dividing {a}, {b}')
            return (temp_ops, 'Int')
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
    # calc_parser = Lark(calc_grammar, parser='lalr')
    # calc = calc_parser.parse
    quack_parser = Lark(quack_grammar, parser='lalr')
    quack = quack_parser.parse
    with open(quack_file) as f:
        input_str = f.read()
    print(input_str)
    tree = MakeAssemblyTree(output_asm)
    # print('---------------------------')
    # POT(quack(input_str))
    print('---------------------------')
    tree.transform(quack(input_str))
    print('---------------------------')
    print(quack(input_str).pretty())
    print('---------------------------')
    # tree.write_to_file()

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: lark_parser.py [input_quack_file] [path/to/output.asm]')
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
