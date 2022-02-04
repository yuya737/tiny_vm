"""A very simple calculator using the Lark parser generator"""

import argparse
import sys
from typing import List, Tuple
from lark import Lark, Transformer
from lark.visitors import Interpreter
import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

def cli():
    cli_parser = argparse.ArgumentParser()
    cli_parser.add_argument("source", type=argparse.FileType("r"),
                            nargs="?", default=sys.stdin)
    args = cli_parser.parse_args()
    return args


calc_grammar = r"""
?start: block

?block: [stmt (";" stmt)*]

?stmt: ifstmt
    | expr

ifstmt: "if" cond "then" expr "else" expr

?cond: cond "and" compare -> bool_and
    | cond "or" compare  -> bool_or
    | compare

compare: expr "<" expr -> less_than
    | expr ">" expr -> greater_than
    | expr "==" expr -> equals

?expr: term
    | expr "+" term -> add
    | expr "-" term -> subtract

?term: factor
    | term "*" factor -> multiply
    | term "/" factor -> divide


factor: NUMBER -> number
NUMBER: /-?[0-9]+/
SEMI: ";"
%import common.WS
%ignore WS
"""

calc_parser = Lark(calc_grammar)

LAB_COUNT = 0
def new_label(prefix: str) -> str:
    global LAB_COUNT
    LAB_COUNT += 1
    return f"{prefix}_{LAB_COUNT}"

class ASTNode:
    """Abstract base class"""
    def r_eval(self) -> List[str]:
        """Evaluate for value"""
        raise NotImplementedError(f"r_eval not implemented for node type {self.__class__.__name__}")

    def c_eval(self, true_branch: str, false_branch: str) -> List[str]:
        raise NotImplementedError(f"c_eval not implemented for node type {self.__class__.__name__}")


class SeqNode(ASTNode):
    """Sequence of statements"""
    def __init__(self, children: List[ASTNode]):
        self.children = children

    def r_eval(self) -> List[str]:
        """Evaluate for value"""
        return [child.r_eval() for child in self.children]

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

class ConstNode(ASTNode):
    """Integer constant"""
    def __init__(self, value: str):
        self.value = value

    def r_eval(self) -> List[str]:
        return [f"const {self.value}"]

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


class ASTBuilder(Transformer):
    """Translate Lark tree to AST"""

    def block(self, e) -> ASTNode:
        return SeqNode(e)

    def ifstmt(self, e) -> ASTNode:
        condpart, thenpart, elsepart = e
        return IfNode(condpart, thenpart, elsepart)

    def bool_and(self, e):
        left, right = e
        return AndNode(left, right)

    def bool_or(self, e):
        left, right = e
        return OrNode(left, right)

    def bool_and(self, e):
        left, right = e
        return AndNode(left, right)

    def less_than(self, e):
        left, right = e
        return ComparisonNode("less", left, right)

    def greater_than(self, e):
        left, right = e
        return ComparisonNode("more", left, right)

    def equals(self, e):
        left, right = e
        return ComparisonNode("equal", left, right)

    def add(self, e):
        left, right = e
        return Arith("add", left, right)

    def subtract(self, e):
        left, right = e
        return Arith("subtract", left, right)

    def number(self, e):
        value = e[0]
        return ConstNode(int(value))

args = cli()
text = "".join(args.source.readlines())
tree = calc_parser.parse(text)
print(tree.pretty("   "))
ast = ASTBuilder().transform(tree)
breakpoint()
print(ast)
objcode = ast.r_eval()
print(objcode)
print("\n".join(objcode))



