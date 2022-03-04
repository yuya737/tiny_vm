import sys
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type, Union
from lark import Lark, Transformer, v_args, Visitor, Tree, Token
from lark.tree import pydot__tree_to_png
from dataclasses import dataclass

import class_hierarchy
from AST_Classes import *

quack_grammar = """
    ?start: program -> root

    program: class* statement*

    class: class_signature "{" constructor_statement_block method_block "}" -> qclass

    class_signature: "class" IDENT "(" formal_args ")" ["extends" IDENT]

    formal_args: [ IDENT ":" IDENT ("," IDENT ":" IDENT)*]

    constructor_statement_block: statement*

    method_block: method*

    method: "def" IDENT "(" formal_args ")" [":" IDENT] statement_block

    statement_block: "{" statement* "}"

    ?statement: rexp ";" -> bare_right_expression
        | typecase
        | assignment ";"
        | ifstmt
        | whilestmt
        | "return" rexp ";" -> return_statement

    typecase: "typecase" rexp "{" type_alternative* "}"

    type_alternative: IDENT ":" IDENT statement_block

    ifstmt: "if" rexp statement_block [("else" statement_block)] -> ifstmt
        | "if" rexp statement_block ("elif" rexp statement_block)+ "else" statement_block -> ifelseifstmt

    whilestmt: "while" rexp statement_block

    methodargs: rexp ("," rexp)*

    assignment: lexpr [":" IDENT] "=" rexp

    ?rexp: and_expr
        | rexp "or" and_expr -> _or

    ?and_expr: not_expr
        | not_expr "and" comparison_expr -> _and

    ?not_expr: comparison_expr
        | "not" not_expr  -> _not

    ?comparison_expr: arith_expr
        | comparison_expr "<=" arith_expr -> leq
        | comparison_expr ">=" arith_expr -> geq
        | comparison_expr "<" arith_expr -> lt
        | comparison_expr ">" arith_expr -> gt
        | comparison_expr "==" arith_expr -> eq

    ?arith_expr: product
        | arith_expr "+" product   -> add
        | arith_expr "-" product   -> sub

    ?product: atom_expr
        | product "*" atom_expr  -> mul
        | product "/" atom_expr  -> div

    ?atom_expr: atom_expr "." IDENT "(" methodargs? ")" -> methodcall
        | atom_expr "." IDENT -> fieldreference
        | IDENT "(" methodargs? ")" -> constructorcall
        | atom

    ?atom: constant
         | lexp
         | "-" atom          -> neg
         | "(" rexp ")"
         | "true" -> true
         | "false" -> false

    lexp: IDENT             -> var_reference
        | "this" "." IDENT  -> this_reference_lexp

    ?lexpr: lexp
        | atom_expr "." IDENT -> fieldreference

    COMMENT: "//" /(.)+/ NEWLINE
        | "/*" /(.|\n)+/x "*/"

    ?constant: INT       -> number
        | ESCAPED_STRING    -> string


    IDENT: /[_a-zA-Z][_a-zA-Z0-9]*/
    %import common.CNAME -> NAME
    %import common.INT
    %import common.ESCAPED_STRING
    %import common.WS
    %import common.NEWLINE

    %ignore WS
    %ignore COMMENT
"""
        # | logic_expr



    # logic_expr
        # | logic_expr "and" rexp -> _and
        # | logic_expr "or" rexp -> _or
        # | rexp "<" rexp -> lt
        # | rexp ">" rexp -> gt

        # | rexp "<=" rexp -> leq
        # | rexp ">=" rexp -> geq
        # | rexp "==" rexp -> eq
        # | rexp "+" product   -> add
        # | rexp "-" product   -> sub
        # | "-" rexp -> neg
        # | "(" rexp ")"
        # | product

    # ?arth_expr:
    #     | rexp "+" rexp -> add
    #     | rexp "-" rexp -> sub
    #     | rexp "*" rexp -> mul
    #     | rexp "/" rexp -> div
    #     | "-" rexp -> neg
    #     | "(" arth_expr ")"


    # ?sum: product
    #     | sum "+" product   -> add
    #     | sum "-" product   -> sub

    # ?product: atom
    #     | product "*" atom  -> mul
    #     | product "/" atom  -> div

    # ?atom: constant
    #     | "-" atom          -> neg
    #     | lexp              -> var_reference
    #     | "(" sum ")"

# tc = None
# var_dict: Dict[str, str] = {}

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
        caller, m_name, *methodargs = lst
        if methodargs:
            methodargs = methodargs[0]
        else:
            methodargs = None
        return MethodcallNode(caller, m_name.value, methodargs)

    def statement(self, lst) -> ASTNode:
        print(f'In statement {lst}')
        return StatementNode(lst[0])

    def statement_block(self, lst) -> ASTNode:
        # breakpoint()
        print(f'In statement_block {lst}')
        return StatementBlockNode(lst)

    def constructor_statement_block(self, lst) -> ASTNode:
        # breakpoint()
        print(f'In constructor statement_block {lst}')
        return ConstructorStatementBlockNode(lst)

    def method_block(self, lst) -> ASTNode:
        # breakpoint()
        print(f'In method {lst}')
        return ClassMethodBlockNode(lst)

    # def methodargs_recur(self, lst) -> ASTNode:
    #     print(f'In methodargs_recur {lst}')
    #     methodargs, constant = lst
    #     return MethodargsrecurNode(methodargs, constant)

    def methodargs(self, lst) -> ASTNode:
        print(f'In methodargs {lst}')
        return MethodargsNode(lst)

    def qclass(self, lst) -> ASTNode:
        print(f'In class {lst}')
        class_signature, constructor_statement_block, method_block = lst
        return ClassNode(class_signature, constructor_statement_block, method_block)

    def class_signature(self, lst) -> ASTNode:
        print(f'In class signature {lst}')
        class_name, formal_args, super_class = lst
        if super_class:
            super_class = super_class.value

        return ClassSignatureNode(class_name.value, formal_args, super_class)

    def formal_args(self, lst) -> ASTNode:
        print(f'In formal args {lst}')
        return FormalArgsNode([item.value for item in lst if item])

    def class_body(self, lst) -> ASTNode:
        print(f'In class body {lst}')
        return ClassBodyNode([item for item in lst if isinstance(item, StatementNode)],
                             [item for item in lst if isinstance(item, ClassMethodNode)])

    def method(self, lst) -> ASTNode:
        method_name, formal_args, ret_type, statement_block = lst
        if ret_type:
            ret_type = ret_type.value
        return ClassMethodNode(method_name.value, formal_args, ret_type, statement_block)


#     def program_recur(self, lst) -> ASTNode:
#         print(f'In program_recur {lst}')
#         program, statement = lst
#         return ProgramrecurNode(program, statement)

    def program(self, lst) -> ASTNode:
        class_list = [item for item in lst if isinstance(item, ClassNode)]
        statement_list = lst[len(class_list):]
        print(f'In program {class_list}, {statement_list}')
        return ProgramNode(class_list, BareStatementBlockNode(statement_list))

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
        print(f'In ifstmt {lst}')
        return IfNode(condpart, thenpart, elsepart)

    def ifelseifstmt(self, lst) -> ASTNode:
        condpart, thenpart, *elifblock, elsepart = lst
        print(f'In ifelseifstmt {lst}')
        elif_node = IfNode(elifblock[-2], elifblock[-1], elsepart)

        # Number of additional elifs to handle
        num_elifs = len(elifblock) / 2 - 1
        counter = 2
        while num_elifs > 0:
            elif_node = IfNode(elifblock[-2*counter], elifblock[-2*counter + 1], elif_node)
            num_elifs -= 1
            counter += 1
        return IfNode(condpart, thenpart, elif_node)

    def whilestmt(self, lst) -> ASTNode:
        condpart, statementblock = lst
        print(f'In whilestmt {lst}')
        return WhileNode(condpart, statementblock)


    def _or(self, lst) -> ASTNode:
        left, right = lst
        print(f'In OR {left}, {right}')
        return OrNode(left, right)

    def _and(self, lst) -> ASTNode:
        left, right = lst
        print(f'In OR {left}, {right}')
        return AndNode(left, right)

    def _not(self, lst) -> ASTNode:
        statement = lst[0]
        print(f'In NOT {statement}')
        return NotNode(statement)

    def eq(self, lst) -> ASTNode:
        left, right = lst
        print(f'In eq {left}, {right}')
        return MethodcallNode(left, 'EQUALS', MethodargsNode([right]))
        # return ComparisonNode(left, right, "==")

    def lt(self, lst) -> ASTNode:
        left, right = lst
        print(f'In lt {left}, {right}')
        return MethodcallNode(left, 'LESS', MethodargsNode([right]))

    def gt(self, lst) -> ASTNode:
        left, right = lst
        print(f'In gt {left}, {right}')
        return MethodcallNode(left, 'MORE', MethodargsNode([right]))

    def geq(self, lst) -> ASTNode:
        left, right = lst
        print(f'In geq {left}, {right}')
        return MethodcallNode(left, 'ATLEAST', MethodargsNode([right]))

    def leq(self, lst) -> ASTNode:
        left, right = lst
        print(f'In leq {left}, {right}')
        return MethodcallNode(left, 'ATMOST', MethodargsNode([right]))


    def type(self, lst) -> str:
        print(f'In type NAME:{lst[0]}')
        return lst[0].value

    def lexp(self, lst) -> ASTNode:
        print(f'In lexp NAME:{lst[0]}')
        return BareLexpNode(lst[0].value)

    def rexp(self, lst) -> ASTNode:
        print(f'In rexp NAME:{lst[0]}')
        return RexpNode(lst[0])

    def bare_right_expression(self, lst) -> ASTNode:
        print(f'In barerexp NAME:{lst[0]}')
        return BareRexpNode(lst[0])

    def var_reference(self, lst) -> ASTNode:
        referenced_variable = lst[0].value
        print(f'In var_reference var:{referenced_variable}')
        return VarReferenceNode(referenced_variable)

    def fieldreference(self, lst) -> ASTNode:
        atomic_expr, field_name = lst
        print(f'In fieldreference {atomic_expr}, {field_name}')
        return FieldReferenceLexpNode(atomic_expr, field_name)

    def this_reference_lexp(self, lst) -> ASTNode:
        print(f'In field_reference_lexp {lst}')
        return ThisReferenceLexpNode(lst[0].value)

    def constructorcall(self, lst) -> ASTNode:
        caller_name, *arguments = lst
        if arguments:
            arguments = arguments[0]
        else:
            arguments = None
        print(f'In constructor call with {caller_name} with arguments {arguments}')
        return ConstructorCall(caller_name.value, arguments)

    def return_statement(self, lst) -> ASTNode:
        print(f'In return {lst}')
        return ReturnStatementNode(lst[0])

    def type_alternative(self, lst) -> ASTNode:
        alt_name, type_name, statement_block = lst
        print(f'In type_alternative {lst}')
        return TypeAlternativeNode(alt_name.value, type_name.value, statement_block)

    # Typecase is a just a glorified if/else
    def typecase(self, lst) -> ASTNode:
        rexp, *type_alternative_list = lst
        print(f'In typecase {lst}')

        def replace_var_reference(node: ASTNode, rexp_to_add: ASTNode, alt_name_reference_node: ASTNode):
            if not node:
                return
            print(node, node.children)
            for i in range(len(node.children)):
                if node.children[i] == alt_name_reference_node:
                    node.children[i] = rexp_to_add
            for child in node.children:
                replace_var_reference(child, rexp_to_add, alt_name_reference_node)

        def typecase_tree_builder(cur_index: int, rexp_to_add: ASTNode) -> IfNode:
            # Add assignment node
            cur_item = type_alternative_list[cur_index]
            assignment_node = AssignmentNode(TypeCaseVarReferenceNode(cur_item.alt_name, cur_item.type_name), cur_item.type_name, rexp)
            cur_item.children[0].children.insert(0, assignment_node)

            # Exchange variable reference to the alt_name with the rexp
            alt_name_reference_node = VarReferenceNode(cur_item.alt_name)

            # replace_var_reference(cur_item.children[0], rexp_to_add, alt_name_reference_node)


            # Base case is the last type_alternative_list item
            if cur_index == len(type_alternative_list) - 1:
                return IfNode(IsInstanceNode(rexp, cur_item.type_name),
                              cur_item.children[0],
                              None)

            else:
                return IfNode(IsInstanceNode(rexp, cur_item.type_name),
                                             cur_item.children[0],
                                             typecase_tree_builder(cur_index + 1, rexp_to_add))

        return typecase_tree_builder(0, rexp)


    # def neg(self, expression: Instr_dtype_pair) -> Instr_dtype_pair:
    def neg(self, lst) -> ASTNode:
        val = lst[0]
        print(f'In neg: {val}')
        return MethodcallNode(ConstNode(0, 'Int'), "MINUS", MethodargsNode([val]))

    def add(self, lst) -> ASTNode:
        val1, val2 = lst
        print(f'In add: {val1}, {val2}')
        return MethodcallNode(val1, "PLUS", MethodargsNode([val2]))

    def sub(self, lst) -> ASTNode:
        val1, val2 = lst
        print(f'In sub: {val1}, {val2}')
        return MethodcallNode(val1, "MINUS", MethodargsNode([val2]))

    def mul(self, lst) -> ASTNode:
        val1, val2 = lst
        print(f'In mul: {val1}, {val2}')
        return MethodcallNode(val1, "TIMES", MethodargsNode([val2]))

    def div(self, lst) -> ASTNode:
        val1, val2 = lst
        print(f'In mul: {val1}, {val2}')
        return MethodcallNode(val1, "DIVIDE", MethodargsNode([val2]))

def type_check(RootNode: ASTNode) -> Dict[str, str]:
    var_dict: Dict[str, str] = {}
    RootNode.type_eval(var_dict)
    # temp_var_dict = var_dict.copy()
    # print('Variables after first pass', var_dict)
    # count = 1
    # while True:
    #     print(f'In type_check iteration number: {count}')
    #     RootNode.type_eval(var_dict)
    #     print(f'Variables after pass numer: {count}', var_dict)
    #     count += 1
    #     if temp_var_dict == var_dict:
    #         break
    #     else:
    #         temp_var_dict = var_dict.copy()
    # print('Finished Type Checking')
    return var_dict

def write_to_file(quack_file: str, RootNode: ASTNode, output_asm: str, var_dict: Dict[str, str]) -> List[str]:
    final_file_list = []
    # instr = RootNode.r_eval(var_dict)
    ProgramNode = RootNode.children[0]

    # Run an initialization check
    ProgramNode.init_check([], False)

    *class_list, bare_statement_block_node = ProgramNode.children
    for qclass in class_list:
        qclass.type_eval({})
    for qclass in class_list:
        class_name = qclass.children[0].class_name
        with open(f'{class_name}.asm', 'w') as f:
            instr = qclass.r_eval({})
            for i in instr:
                # Replace self constructor and field reference on 'self', except class declaration
                if i == f'\tnew {class_name}':
                    i = '\tnew $'
                if (i.startswith('\tstore') or i.startswith('\tload') or i.startswith('\tcall')) and f'{class_name}:' in i:
                    i = i.replace(f'{class_name}:', '$:')
                if (i == f'\tis_instance {class_name}'):
                    i = '\tis_instance $'
                f.write(i)
                f.write('\n')
        final_file_list.append(class_name)

    with open(output_asm + '_main.asm', 'w') as f:
        bare_statement_block_local_var_dict = {}
        bare_statement_block_node.type_eval(bare_statement_block_local_var_dict)
        instr = bare_statement_block_node.r_eval(bare_statement_block_local_var_dict)
        f.write(f".class {output_asm + '_main'}:Obj\n")
        f.write('\n')
        f.write('.method $constructor\n')
        bare_statement_block_local_var_list = [item[1] if isinstance(item, tuple) else item for item in bare_statement_block_local_var_dict.keys()]
        if bare_statement_block_local_var_list:
            f.write(f".local {','.join(bare_statement_block_local_var_list)}\n")
        for i in instr:
            f.write(i)
            f.write('\n')
        f.write('\tconst nothing\n')
        f.write('\treturn 0\n')

    print('\nPrinting Class Hierarchy')
    print_class_hierarchy()
    print('------------------------------------------------------')

    final_file_list.append(output_asm + '_main')
    return final_file_list


def ast_pydot__tree_to_png(tree: ASTNode, filename: str, rankdir: 'Literal["TB", "LR", "BT", "RL"]'="LR", **kwargs) -> None:
    graph = pydot__tree_to_graph(tree, rankdir, **kwargs)
    graph.write_png(filename)


def pydot__tree_to_dot(tree: ASTNode, filename, rankdir="LR", **kwargs):
    graph = pydot__tree_to_graph(tree, rankdir, **kwargs)
    graph.write(filename)


def pydot__tree_to_graph(tree: ASTNode, rankdir="LR", **kwargs):

    import pydot  # type: ignore[import]
    graph = pydot.Dot(graph_type='digraph', rankdir=rankdir, **kwargs)

    i = [0]

    def new_leaf(leaf):
        label = leaf.pretty_label() if leaf else 'NONE'
        node = pydot.Node(i[0], label=label)
        i[0] += 1
        graph.add_node(node)
        return node

    def _to_pydot(subtree):

        color = hash(subtree.__class__.__name__) & 0xffffff
        color |= 0x808080

        subnodes = [_to_pydot(child) if child and len(child.children) > 0 else new_leaf(child)
                    for child in subtree.children]

        node = pydot.Node(i[0], style="filled", fillcolor="#%x" % color, label=subtree.pretty_label())
        i[0] += 1
        graph.add_node(node)

        for subnode in subnodes:
            graph.add_edge(pydot.Edge(node, subnode))

        return node

    _to_pydot(tree)
    return graph


def main(quack_file, output_asm, builtinclass_json):
    quack_parser = Lark(quack_grammar, parser='lalr')
    # quack_parser = Lark(quack_grammar)
    quack = quack_parser.parse
    with open(quack_file) as f:
        input_str = f.read()
    print(input_str)
    parse_builtin_classes(builtinclass_json)
    tree = MakeAssemblyTree(output_asm)
    print('------------------------------------------------------')
    print(quack(input_str).pretty())
    print('------------------------------------------------------')
    ast = tree.transform(quack(input_str))
    print('------------------------------------------------------')
    # pydot__tree_to_png(quack(input_str), 'CST.png')
    # ast_pydot__tree_to_png(ast, 'AST.png')
    print('Printing Transformed AST')
    pretty_print(ast)
    print('------------------------------------------------------')
    final_file_list = write_to_file(quack_file, ast, output_asm, {})
    with open('final_file_list', 'w') as f:
        for i in final_file_list:
            f.write(i + ' ')

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print('Usage: lark_parser.py [input_quack_file] [path/to/output.asm] [path/to/builtinclass.json]')
        sys.exit(1)
    main(sys.argv[1], sys.argv[2], sys.argv[3])
