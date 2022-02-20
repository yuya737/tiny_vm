from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type, Union

import class_hierarchy

ch: class_hierarchy.RootObjClass

class ASTNode:
    """Abstract base class"""
    def __init__(self) -> None:
        self.children: List[ASTNode] = []

    def r_eval(self, local_var_dict: Dict[str, str]) -> Optional[List[str]]:
        """Evaluate for value"""
        raise NotImplementedError(f"r_eval not implemented for node type {self.__class__.__name__}")

    def l_eval(self) -> Optional[List[str]]:
        """Evaluate for value"""
        raise NotImplementedError(f"r_eval not implemented for node type {self.__class__.__name__}")

    def c_eval(self, true_branch: str, false_branch: str, local_var_dict: Dict[str, str]) -> Optional[List[str]]:
        raise NotImplementedError(f"c_eval not implemented for node type {self.__class__.__name__}")

    def type_eval(self, local_var_dict: Dict[str, str]) -> Optional[str]:
        raise NotImplementedError(f"type_eval not implemented for node type {self.__class__.__name__}")

    def init_check(self, local_var_list: List[str], in_constructor: bool) -> None:
        raise NotImplementedError(f"init_check not implemented for node type {self.__class__.__name__}")

    def pretty_label(self) -> str:
        raise NotImplementedError(f"pretty_label not implemented for node type {self.__class__.__name__}")


LAB_COUNT = 0
def new_label(prefix: str) -> str:
    global LAB_COUNT
    LAB_COUNT += 1
    return f"{prefix}_{LAB_COUNT}"

def pretty_helper(node: ASTNode, level: int, indent_str: str) -> List[str]:
    print(node)
    # print(node.children)
    if len(node.children) == 0:
        return [indent_str*level, node.pretty_label(), '\n']

    l = [indent_str*level, node.pretty_label(), '\n']
    # print(l)
    for n in node.children:
        if n:
            l += pretty_helper(n, level+1, indent_str)

    return l

def pretty_print(RootNode: ASTNode) -> None:
    print(''.join(pretty_helper(RootNode, 0, '  ')))

def populate_local_var_dict_with_initialized_vars(local_var_dict: Dict[str, str], local_var_list: List[str]):
    for initialized_var in local_var_list:
        if initialized_var not in local_var_dict:
            # Add as None
            local_var_dict[initialized_var] = None


class RootNode(ASTNode):
    """Sequence of statements"""
    def __init__(self, program: ASTNode):
        super().__init__()
        self.children.append(program)

    def r_eval(self, local_var_dict: Dict[str, str]):
        """Evaluate for value"""
        program = self.children[0]
        return program.r_eval(local_var_dict)

    def type_eval(self, local_var_dict: Dict[str, str]):
        """Evaluate for value"""
        program = self.children[0]
        return program.type_eval(local_var_dict)

    def pretty_label(self) -> str:
        return "RootNode"


class IfNode(ASTNode):
    """if cond then block else block"""
    def __init__(self, condpart: ASTNode, thenpart: ASTNode, elsepart: ASTNode) -> None:
        super().__init__()
        self.children.append(condpart)
        self.children.append(thenpart)
        if elsepart:
            self.children.append(elsepart)

    def r_eval(self, local_var_dict: Dict[str, str]):
        """Evaluate for value"""
        if len(self.children) == 2:
            condpart, thenpart = self.children
            elsepart = []
        else:
            condpart, thenpart, elsepart = self.children

        then_label = new_label("then")
        else_label = new_label("else")
        endif_label = new_label("endif")
        iftest = condpart.c_eval(then_label, else_label, local_var_dict)
        thenblock = thenpart.r_eval(local_var_dict)
        elseblock = elsepart.r_eval(local_var_dict) if elsepart else []
        return (iftest
                + [then_label + ":"]
                + thenblock
                + [f"\tjump {endif_label}"]
                + [else_label + ":"]
                + elseblock
                + [endif_label + ":"])

    def type_eval(self, local_var_dict: Dict[str, str]):
        # KEY THING FOR IFNODE in constructors:
        #   -   Single if can't define any new fields. In other words, var_dict after and before should have
        #       the same vars that have the form this.--
        #   -   If-else can't define different fields. So, var_dict after then and after else should have
        #       the same vars taht have the form this.--


        # Keep track for potential return statements
        final_ret_type = None

        if len(self.children) == 2:
            condpart, thenpart = self.children
            var_dict_before_if = local_var_dict

            var_dict_after_if = local_var_dict.copy()

            final_ret_type = thenpart.type_eval(var_dict_after_if)

            # Update local_var_dict - (only need to update item types. Since single if can't add new variables, the only thing that happens is taking the LCA of variables that was previously declared. var_dict never loses or adds items here)
            for new_item in var_dict_after_if:
                if new_item in local_var_dict:
                    local_var_dict[new_item] = ch.find_LCA(var_dict_after_if[new_item], local_var_dict[new_item])


        else:
            condpart, thenpart, elsepart = self.children

            var_dict_before_if = local_var_dict

            var_dict_after_then = local_var_dict.copy()
            thenpart_ret_type = thenpart.type_eval(var_dict_after_then)

            # Update return type of the statement bloc
            # final_ret_type = ch.find_LCA(final_ret_type, thenpart_ret_type) if thenpart_ret_type else pass
            if thenpart_ret_type:
                if final_ret_type:
                    final_ret_type = ch.find_LCA(final_ret_type, thenpart_ret_type)
                else:
                    final_ret_type = thenpart_ret_type

            var_dict_after_else = local_var_dict.copy()
            elsepart_ret_type = elsepart.type_eval(var_dict_after_else)

            # Update return type of the statement bloc
            # final_ret_type = ch.find_LCA(final_ret_type, elsepart_ret_type) if final_ret_type else elsepart_ret_type
            if elsepart_ret_type:
                if final_ret_type:
                    final_ret_type = ch.find_LCA(final_ret_type, elsepart_ret_type)
                else:
                    final_ret_type = elsepart_ret_type

            # Construct new var_dict as an intersection of items. When there is an overlap assign the LCA
            new_dict_keys = var_dict_after_then.keys() & var_dict_after_else.keys()
            new_dict = {}

            for new_dict_key in new_dict_keys:
                new_dict[new_dict_key] = ch.find_LCA(var_dict_after_then[new_dict_key], var_dict_after_else[new_dict_key])

            # Update the passed local_var_dict (only need to add items, var_dict never loses items here)
            for new_item in new_dict:
                local_var_dict[new_item] = new_dict[new_item]

        # Make sure that the condpart actually evaluates to a Boolean
        if condpart.type_eval(local_var_dict) != "Boolean":
            raise TypeError("If statement expects the condition to return a Boolean")

        return final_ret_type

    def init_check(self, local_var_list: List[str], in_constructor: bool):

        if len(self.children) == 2:
            condpart, thenpart = self.children
            condpart.init_check(local_var_list, in_constructor)
            # condpart has no initialization

            var_dict_before_if = local_var_list
            var_dict_after_if = local_var_list.copy()
            thenpart.init_check(var_dict_after_if, in_constructor)

            # Single if can't define any new class fields in the constructor
            # if in_constructor:
            #     if set([item for item in var_dict_before_if if item.startswith('this.')]) != set([item for item in var_dict_after_if if item.startswith('this.')]):
            #         raise SyntaxError(f'Single if statements in constructors can not define new field variables.')
        else:
            condpart, thenpart, elsepart = self.children
            condpart.init_check(local_var_list, in_constructor)

            var_dict_before_if = local_var_list

            var_dict_after_then = local_var_list.copy()
            thenpart_ret_type = thenpart.init_check(var_dict_after_then, in_constructor)

            var_dict_after_else = local_var_list.copy()
            elsepart_ret_type = elsepart.init_check(var_dict_after_else, in_constructor)

            # local_var_list doesn't lose values
            for i in list(set(var_dict_after_then) & set(var_dict_after_else)):
                if i not in local_var_list:
                    local_var_list.append(i)

            # # If if-else is in the constructor, make sure that both branches define the same field variables
            # if in_constructor:
            #     if set([item for item in var_dict_after_then if item.startswith('this.')]) != set([item for item in var_dict_after_else if item.startswith('this.')]):
            #         breakpoint()
            #         raise SyntaxError(f'Control flows inside constructor block need to define the same field variables.')
        return None


    def pretty_label(self) -> str:
        if len(self.children) == 2:
            return "IfNode"
        else:
            return "IfElseNode"


class WhileNode(ASTNode):
    """if cond then block else block"""
    def __init__(self, condpart: ASTNode, statementblock: ASTNode):
        super().__init__()
        self.children.append(condpart)
        self.children.append(statementblock)

    def r_eval(self, local_var_dict: Dict[str, str]):
        """Evaluate for value"""
        condpart, statementblock = self.children
        loophead = new_label("loop_head")
        looptest = new_label("loop_test")
        nextStmt = new_label("done")

        block = statementblock.r_eval(local_var_dict)

        whiletest = condpart.c_eval(loophead, nextStmt, local_var_dict)
        return ([f'jump {looptest}']
                + [loophead + ":"]
                + block
                + [looptest + ":"]
                + whiletest
                + [nextStmt + ":"])

    def type_eval(self, local_var_dict: Dict[str, str]):
        condpart, statementblock = self.children
        var_dict_before_block = local_var_dict

        # Pass in a copy of local_var_dict to type eval because new variables in while are to be ignored after the loop
        var_dict_after_block = local_var_dict.copy()
        statementblock_ret_type = statementblock.type_eval(var_dict_after_block)

        # Update local_var_dict - (only need to update item types. Since while can't add new variables, the only thing that happens is taking the LCA of variables that was previously declared. var_dict never loses or adds items here)
        for new_item in var_dict_after_block:
            if new_item in var_dict_before_block:
                local_var_dict[new_item] = ch.find_LCA(var_dict_after_block[new_item], var_dict_before_block[new_item])

        if condpart.type_eval(local_var_dict) != "Boolean":
            raise TypeError("If statement expects the condition to return a Boolean")

        return statementblock_ret_type

    def init_check(self, local_var_list: List[str], in_constructor: bool):
        condpart, statementblock = self.children
        var_dict_before_block = local_var_list.copy()

        # Pass in a copy of local_var_list to type eval because new variables in while are to be ignored after the loop
        var_list_after_block = local_var_list.copy()
        statementblock_ret_type = statementblock.init_check(var_list_after_block, in_constructor)

        # # While can't define any new class fields in the constructor
        # if in_constructor:
        #     if set([item for item in var_dict_before_block if item.startswith('this.')]) != set([item for item in var_dict_after_block if item.startswith('this.')]):
        #         raise SyntaxError(f'While loop in constructors can not define new field variables.')

        # Local var dict should be untouched
        return None


    def pretty_label(self) -> str:
        return "WhileNode"


class MethodcallNode(ASTNode):
    """Method call node"""
    def __init__(self, caller: ASTNode, m_name: str, methodargs: ASTNode):
        super().__init__()
        self.children.append(caller)
        self.children.append(methodargs)
        self.m_name = m_name

        # Type checking will check the caller type - can be a superclass
        self.caller_type = None

    def r_eval(self, local_var_dict: Dict[str, str]):
        caller, methodargs = self.children
        methodargs_r_eval = methodargs.r_eval(local_var_dict) if methodargs else []
        caller_type = self.caller_type
        return (methodargs_r_eval
                + caller.r_eval(local_var_dict)
                + [f'\tcall {caller_type}:{self.m_name}'])

    def type_eval(self, local_var_dict: Dict[str, str]):
        caller, methodargs = self.children
        caller_type = caller.type_eval(local_var_dict)

        # print(caller.r_eval())
        # print('In methodcall type eval')
        quackClassEntry = ch.find_class(caller_type)

        # Make sure this function exists
        quackFunctionEntry = [entry for entry in quackClassEntry.methods_list if entry.method_name == self.m_name]
        # Check its superclass in order, if its not defined in this class
        if not quackFunctionEntry:
            method_found_in_a_superclass = False
            # path to subclass reversed, but itself
            super_class_chain = ch.get_path_to_subclass(caller_type)[-2::-1]
            for super_class in super_class_chain:
                quackFunctionEntry = [entry for entry in ch.find_class(super_class).methods_list if entry.method_name == self.m_name]
                if quackFunctionEntry: # If the function is found in a super class edit the caller type
                    method_found_in_a_superclass = True
                    caller_type = super_class
                    break

            if not method_found_in_a_superclass:
                raise NotImplementedError(f'Function {self.m_name} for {caller_type} is not defined or by any of its super classes {super_class_chain}')

        quackFunction = quackFunctionEntry[0]


        # Make sure that the arguments are the right type. If there are no arguments, make sure that the funtion is supposed to take no parameters
        args_types = methodargs.type_eval(local_var_dict) if methodargs else []
        ch.is_legal_invocation(caller_type, self.m_name, args_types)
        self.caller_type = caller_type

        return quackFunction.ret

    def init_check(self, local_var_list: List[str], in_constructor: bool):
        caller, methodargs = self.children

        # methodargs doesn't need any init check
        caller.init_check(local_var_list, in_constructor)
        return None

    def c_eval(self, true_branch: str, false_branch: str, local_var_dict: Dict[str, str]) -> List[str]:
        bool_code = self.r_eval(local_var_dict)
        return bool_code + [f"\tjump_if {true_branch}", f"\tjump {false_branch}"]

    def pretty_label(self) -> str:
        return f"MethodcallNode: {self.m_name}"


class StatementNode(ASTNode):
    """Statement node"""
    def __init__(self, statement: ASTNode):
        super().__init__()
        self.children.append(statement)

    def r_eval(self, local_var_dict: Dict[str, str]):
        return self.children[0].r_eval(local_var_dict)

    def type_eval(self, local_var_dict: Dict[str, str]):
        return self.children[0].type_eval(local_var_dict)

    def init_check(self, local_var_list: List[str], in_constructor: bool):
        self.children[0].init_check(local_var_list, in_constructor);
        return None

    # def get_field_variables(self, field_var_dict: Dict[str, str], temp_local_var_dict: Dict[str, str]):
    #     for child in self.children:
    #         if isinstance(child, AssignmentNode):
    #             child.get_field_variables(field_var_dict, temp_local_var_dict)

    def pretty_label(self) -> str:
        return "StatementNode"

class ReturnStatementNode(ASTNode):
    """Return Statement node"""
    def __init__(self, statement: ASTNode):
        super().__init__()
        self.children.append(statement)

    def r_eval(self, local_var_dict: Dict[str, str]):
        # Add the return line but delagate filling this to the ClassMethodNode
        return self.children[0].r_eval(local_var_dict) + ['\treturn TOFILL']

    def type_eval(self, local_var_dict: Dict[str, str]):
        return self.children[0].type_eval(local_var_dict)

    def init_check(self, local_var_list: List[str], in_constructor: bool):
        if in_constructor:
            raise SyntaxError("Can't call return inside the constructor statement block")
        self.children[0].init_check(local_var_list, in_constructor)
        return None


    # def get_field_variables(self, field_var_dict: Dict[str, str], temp_local_var_dict: Dict[str, str]):
    #     for child in self.children:
    #         if isinstance(child, AssignmentNode):
    #             child.get_field_variables(field_var_dict, temp_local_var_dict)

    def pretty_label(self) -> str:
        return "ReturnStatementNode"

class StatementBlockNode(ASTNode):
    """Statement node"""
    def __init__(self, statement_block: List[ASTNode]):
        super().__init__()
        self.children += statement_block

    def r_eval(self, local_var_dict: Dict[str, str]):
        return [subitem for statement in self.children for subitem in statement.r_eval(local_var_dict)]

    def type_eval(self, local_var_dict: Dict[str, str]):
        final_ret_type = None

        # For each statement, run a type check. If it has a potential to have a return statement - i.e. ifstmt, whilestmt or a return statement update final_ret_type
        for statement in self.children:
            cur_ret_type = statement.type_eval(local_var_dict)
            if isinstance(statement, IfNode) or isinstance(statement, WhileNode) or isinstance(statement, ReturnStatementNode):
                if not final_ret_type: # If no return type was previously assigned...
                    final_ret_type = cur_ret_type
                elif not cur_ret_type: # If the current line doesn't return anything continue
                    continue
                else: # Otherwise, assign the LCA
                    final_ret_type = ch.find_LCA(cur_ret_type, final_ret_type)

        return final_ret_type

    def init_check(self, local_var_list: List[str], in_constructor: bool):
        for statement in self.children:
            cur_ret_type = statement.init_check(local_var_list, in_constructor)
        return None

    def pretty_label(self) -> str:
        return f"StatementBlockNode: length {len(self.children)}"

class ProgramNode(ASTNode):
    """Class  Node"""
    def __init__(self, class_list: List[ASTNode], BareStatementBlockNode: ASTNode):
        super().__init__()
        # self.children.append(program)
        self.children += class_list
        self.children.append(BareStatementBlockNode)
        # self.num_classes = len(class_list)

    def r_eval(self, local_var_dict: Dict[str, str]):
        return ([subitem for child in self.children for subitem in child.r_eval(local_var_dict)])

    def type_eval(self, local_var_dict: Dict[str, str]):
        for child in self.children:
            child.type_eval(local_var_dict)
        return None

    def init_check(self, local_var_list: List[str], in_constructor: bool):
        for child in self.children:
            child.init_check(local_var_list, in_constructor)
        return None

    def pretty_label(self) -> str:
        return "ProgramNode"

class ClassNode(ASTNode):
    """Class Node"""
    def __init__(self, class_signature: ASTNode, constructor_statement_block: ASTNode, method_block: ASTNode):
        super().__init__()
        self.children.append(class_signature)
        self.children.append(constructor_statement_block)
        self.children.append(method_block)

        # Type checking will populate these fields
        self.constructor_scope_local_var_dict = None
        self.method_scope_local_var_dict = None

        # Initialization check will populate these fields
        self.constructor_scope_local_var_list = None
        self.method_scope_local_var_list = None

    def r_eval(self, local_var_dict: Dict[str, str]):
        class_signature, constructor_statement_block, method_block  = self.children
        # Need to pass the number of arguments in the constructor to generate the correct return statement
        return (class_signature.r_eval(self.constructor_scope_local_var_dict) +
                constructor_statement_block.r_eval(self.constructor_scope_local_var_dict, len(class_signature.children[0].arg_names)) +
                method_block.r_eval(self.method_scope_local_var_dict))

    def type_eval(self, local_var_dict: Dict[str, str]):
        global ch
        class_signature, constructor_statement_block, method_block = self.children
        class_name = class_signature.class_name
        super_class = class_signature.super_class
        class_formal_args = class_signature.children[0]

        class_signature.type_eval(local_var_dict)

        # Populate constructor_scope_local_var_dict with list fetched from init_check
        constructor_scope_local_var_dict = local_var_dict.copy()
        populate_local_var_dict_with_initialized_vars(constructor_scope_local_var_dict, self.constructor_scope_local_var_list)

        # Populate types in constructor_scope_local_var_dict
        for constructor_parameter_name, constructor_parameter_type in zip(class_formal_args.arg_names, class_formal_args.arg_types):
            # print('Adding: ', constructor_parameter_name, constructor_parameter_type)
            constructor_scope_local_var_dict[constructor_parameter_name] = constructor_parameter_type

        count = 1
        print(f'In Class constructor type check iteration number: {count}')
        constructor_statement_block.type_eval(constructor_scope_local_var_dict)
        print(constructor_scope_local_var_dict)

        temp_constructor_scope_local_var_dict = constructor_scope_local_var_dict.copy()
        # Try additional passes through to make sure that variable types don't change
        while True:
            count += 1
            print(f'In Class constructor type check iteration number: {count}')
            constructor_statement_block.type_eval(constructor_scope_local_var_dict)
            print(constructor_scope_local_var_dict)
            if temp_constructor_scope_local_var_dict == constructor_scope_local_var_dict:
                break
            else:
                print(f'Constructor type check additional pass detected type changes. Making another pass. Newly interpreted types {constructor_scope_local_var_dict}')
                temp_constructor_scope_local_var_dict = constructor_scope_local_var_dict.copy()


        # Save the variable dictionary for the constructor scope
        self.constructor_scope_local_var_dict = constructor_scope_local_var_dict.copy()


        field_var_dict = {}
        # When type evaluating with a class, treat 'this.x' as its own variable, also add to field_var_dict
        for item in constructor_scope_local_var_dict.keys():
            if item.startswith('this.'):
                local_var_dict[item] = constructor_scope_local_var_dict[item]
                # field_var_dict[item.lstrip('this.')] = constructor_scope_local_var_dict[item]
                field_var_dict[item[5:]] = constructor_scope_local_var_dict[item]

        # Make sure every field that its superclass defines is defined with a compatible assignment
        for superclass_field_name, superclass_field_type in ch.find_class(super_class).fields_list.items():
            if superclass_field_name not in field_var_dict:
                raise TypeError(f"{class_name}'s superclass {super_class} defines {superclass_field_name} but {class_name} does not")
            if not ch.is_legal_assignment(superclass_field_type, field_var_dict[superclass_field_name]):
                raise TypeError(f"{class_name}'s superclass {super_class} defines {superclass_field_name} as an {superclass_field_type} and {field_var_dict[superclass_field_name]} is not a compatible assignment")


        # Add class to class hierachy

        # Add constructor to the method list
        methods_list = [class_hierarchy.QuackClassMethod('$constructor', class_formal_args.arg_types, class_name)]

        for method_node in method_block.children:
            method_name = method_node.method_name
            # children[0] gets the formal_args node
            params_list = method_node.children[0].arg_types
            ret_type = method_node.ret_type
            methods_list.append(class_hierarchy.QuackClassMethod(method_name, params_list, ret_type))

        new_class_to_add = class_hierarchy.QuackClass(class_name, super_class, methods_list, field_var_dict)
        ch.add_class_to_hierarchy(new_class_to_add)
        class_hierarchy.pretty_print(ch)

        # Populate constructor_scope_local_var_dict with list fetched from init_check
        method_scope_local_var_dict = local_var_dict.copy()
        populate_local_var_dict_with_initialized_vars(method_scope_local_var_dict, self.method_scope_local_var_list)
        # Save the variable dictionary for the method scope
        self.method_scope_local_var_dict = method_scope_local_var_dict.copy()

        # Type check the class methods
        method_block.type_eval(method_scope_local_var_dict)

    def init_check(self, local_var_list: List[str], in_constructor: bool):
        class_signature, constructor_statement_block, method_block = self.children

        constructor_statement_block_local_var_list = local_var_list.copy()
        # Add the constructor parameters to the local_var_list
        class_formal_args = class_signature.children[0]
        for constructor_parameter_name in class_formal_args.arg_names:
            constructor_statement_block_local_var_list.append(constructor_parameter_name)


        # class_signature doesn't need a init_check
        constructor_statement_block.init_check(constructor_statement_block_local_var_list, True)
        self.constructor_scope_local_var_list = constructor_statement_block_local_var_list.copy()

        method_block_local_var_list = local_var_list.copy()

        # Add class variables to method_scope_local_var_list
        for item in constructor_statement_block_local_var_list:
            if item.startswith('this') and item not in method_block_local_var_list:
                method_block_local_var_list.append(item)

        method_block.init_check(method_block_local_var_list, in_constructor)
        self.method_scope_local_var_list = method_block_local_var_list.copy()
        return None

    def pretty_label(self) -> str:
        return "ClassNode"

class ConstructorStatementBlockNode(ASTNode):
    """Constructor Statement Block Node"""
    def __init__(self, statement_list: List[ASTNode]):
        super().__init__()
        self.children += statement_list

    def r_eval(self, local_var_dict: Dict[str, str], num_constructor_arguments: int):
        ret = []
        for statement in self.children:
            ret += statement.r_eval(local_var_dict)

        ret += ['\tload $', f'\treturn {num_constructor_arguments}']
        return ret


    def type_eval(self, local_var_dict: Dict[str, str]):
        for child in self.children:
            child.type_eval(local_var_dict)
        return None

    def init_check(self, local_var_list: List[str], in_constructor: bool):
        for child in self.children:
            child.init_check(local_var_list, in_constructor)
        self.initialized_variables = local_var_list.copy()
        return None

    def pretty_label(self) -> str:
        return f"ConstructorStatementBlockNode: length {len(self.children)}"

class ClassMethodBlockNode(ASTNode):
    """Class Method Block Node"""
    def __init__(self, methods_list: List[ASTNode]):
        super().__init__()
        self.children += methods_list

    def r_eval(self, local_var_dict: Dict[str, str]):
        ret = []
        for child in self.children:
            ret += child.r_eval(local_var_dict.copy())
        return ret

    def type_eval(self, local_var_dict: Dict[str, str]):
        for method in self.children:
            count = 1
            print(f'In Class method type check for {method.method_name} iteration number: {count}')
            cur_local_var_dict = local_var_dict.copy()
            method.type_eval(cur_local_var_dict)
            print(cur_local_var_dict)

            # Try additional passes through to make sure that variable types don't change
            temp_cur_local_var_dict = cur_local_var_dict.copy()
            while True:
                count += 1
                print(f'In Class method type check for {method.method_name} iteration number: {count}')
                method.type_eval(cur_local_var_dict)
                print(cur_local_var_dict)
                if temp_cur_local_var_dict == cur_local_var_dict:
                    break
                else:
                    print(f'Class method type check additional pass detected type changes. Making another pass. Newly interpreted types {cur_local_var_dict}')
                    temp_cur_local_var_dict = cur_local_var_dict.copy()

    def init_check(self, local_var_list: List[str], in_constructor: bool):
        for child in self.children:
            child.init_check(local_var_list, in_constructor)
        return None


    def pretty_label(self) -> str:
        return "ClassMethodBlockNode"


# class ClassBodyNode(ASTNode):
#     """Class Body Node"""
#     def __init__(self, statement_list: List[ASTNode], method_list: List[ASTNode]):
#         super().__init__()
#         self.children += statement_list
#         self.children += method_list
#         self.num_constructor_statement = len(statement_list)

#     def r_eval(self, local_var_dict: Dict[str, str], num_constructor_arguments: int):
#         ret = []
#         statement_list = self.children[:self.num_constructor_statement]
#         method_list = self.children[self.num_constructor_statement:]

#         # Constructor lines
#         for statement in statement_list:
#             ret += statement.r_eval(local_var_dict)

#         ret += ['\tload $', f'\treturn {num_constructor_arguments}']

#         # Class Methods
#         for method in method_list:
#             ret += method.r_eval(local_var_dict)

#         return ret

#     def type_eval(self, local_var_dict: Dict[str, str]):
#         for child in self.children:
#             child.type_eval(local_var_dict)
#         return None

#     # Get a list of field variables
#     def get_field_variables(self, field_var_dict: Dict[str, str], temp_local_var_dict: Dict[str, str]) -> None:
#         for possible_field_assignment in self.children[:self.num_constructor_statement]:
#             possible_field_assignment.get_field_variables(field_var_dict, temp_local_var_dict)

#     def pretty_label(self) -> str:
#         return "ClassBodyNode"

# class ReturnNode(ASTNode):
#     """Return statment node"""
#     def __init__(self, rexp: ASTNode):
#         super().__init__()
#         self.children.append(rexp)

#     def r_eval(self, local_var_dict: Dict[str, str]):
#         return



class ClassSignatureNode(ASTNode):
    """Class Signature Node"""
    def __init__(self, class_name: str,  formal_args: ASTNode, super_class: str):
        super().__init__()
        self.class_name = class_name
        self.children.append(formal_args)
        if super_class:
            self.super_class = super_class
        else:
            self.super_class = "Obj"

    def r_eval(self, local_var_dict: Dict[str, str]):

        # Write out the class declaration
        class_declaration = [f'.class {self.class_name}:{self.super_class}']

        # Write out class fieds
        field_declaration = []
        for variable in ch.find_class(self.class_name).fields_list:
            field_declaration += [f'.field {variable}']

        # Write out method forward declarations
        method_forward_declaration = []
        for method in ch.find_class(self.class_name).methods_list:
            method_forward_declaration += [f'.method {method.method_name} forward']

        # Write out constructor declaration
        constructor_declaration = ['.method $constructor']
        formal_args = self.children[0]
        if formal_args.arg_names:
            constructor_declaration += [f".args {','.join(formal_args.arg_names)}"]

        return class_declaration + field_declaration + method_forward_declaration + constructor_declaration

    def type_eval(self, local_var_dict: Dict[str, str]) -> None:
        formal_args = self.children[0]
        # Make sure every constructor parameter has a valid class
        for constructor_parameter_type in formal_args.arg_types:
            if not ch.find_class(constructor_parameter_type):
                raise TypeError(f'Type {constructor_parameter_type} defined in constructor is an invalid type')
        # If a super_class is defined, make sure it actually exists
        if self.super_class and not ch.find_class(self.super_class):
            raise TypeError(f'{self.class_name} specifies {self.super_class} as its super class but it does not exist')

        return None


    def pretty_label(self) -> str:
        return f"ClassSignatureNode - {self.class_name}, SuperClass: {self.super_class}"

class ClassMethodNode(ASTNode):
    """Class Method"""
    def __init__(self, method_name: str, formal_args: ASTNode, ret_type: str, statement_block: ASTNode):
        super().__init__()
        self.children.append(formal_args)
        self.children.append(statement_block)
        self.method_name = method_name

        # var_dict for the current method scope. type_eval will populate this
        self.method_scope_local_var_dict = None

        # var_list for the current method scope. init_check will populate this
        self.method_scope_local_var_list = None

        # If a return type isn't specified, assume that it returns 'Nothing'
        if not ret_type:
            self.ret_type = 'Nothing'
        else:
            self.ret_type = ret_type

    def r_eval(self, local_var_dict: Dict[str, str]):
        formal_args, statement_block = self.children
        args_declaration = [f".args {','.join(formal_args.arg_names)}"] if formal_args.arg_names else []

        # Add local arguments to local_var_dict
        for i in range(len(formal_args.arg_names)):
            local_var_dict[formal_args.arg_names[i]] = formal_args.arg_types[i]

        statement_block_instructions = statement_block.r_eval(self.method_scope_local_var_dict)
        # Write out method declaration
        method_declaration = [f'.method {self.method_name}']

        # Local variables in a function is everyhing that local_var_dict picks out that isn't a field or a function variable
        local_vars_in_function = [item for item in self.method_scope_local_var_dict if item not in formal_args.arg_names and not item.startswith('this.')]

        # Write out local variable declaration
        if local_vars_in_function:
            local_var_declaration = [f".local {','.join(local_vars_in_function)}"]
        else:
            local_var_declaration = []

        # Edit return line, if it exists, otherwise append a return line
        num_class_method_arguments = len(self.children[0].arg_names)
        is_there_a_return_statement = [instruction.startswith('\treturn') for instruction in statement_block_instructions]
        if any(is_there_a_return_statement):
            # If there is a return statement, replace it
            index_of_trues = [index for index, value in enumerate(is_there_a_return_statement) if value]
            for return_statement_index in index_of_trues:
                statement_block_instructions[return_statement_index] = statement_block_instructions[return_statement_index].replace('TOFILL', str(num_class_method_arguments))
        else:
            # Otherwise, add a return
            statement_block_instructions.append('\tconst nothing')
            statement_block_instructions.append(f'\treturn {num_class_method_arguments}')

        return method_declaration + args_declaration + local_var_declaration + statement_block_instructions

    def type_eval(self, local_var_dict: Dict[str, str]):
        formal_args, statement_block = self.children

        method_scope_local_var_dict = local_var_dict

        # Make sure method method parameter has a valid class
        for method_parameter_type in formal_args.arg_types:
            if not ch.find_class(method_parameter_type):
                raise TypeError(f'{method_parameter_type} defined as a parameter in {self.method_name} is an invalid type')

        # Add arguments to local_var_dict
        for method_parameter_name, method_parameter_type in zip(formal_args.arg_names, formal_args.arg_types):
            method_scope_local_var_dict[method_parameter_name] = method_parameter_type

        # Populate local_var_dict with local variables
        populate_local_var_dict_with_initialized_vars(method_scope_local_var_dict, self.method_scope_local_var_list)

        statement_block_ret_type = statement_block.type_eval(method_scope_local_var_dict)
        print(self.method_name, statement_block_ret_type)

        # If the statement block returns something make sure it is a valid return type with the declared return type. If the block returns nothing, make sure there is no return type defined, or that the method is declared to return nothing
        if statement_block_ret_type:
            if not ch.is_legal_assignment(self.ret_type, statement_block_ret_type):
                raise TypeError(f'Function declared to return {self.ret_type} but returns {statement_block_ret_type} instead.')
        else:
            if self.ret_type and not (self.ret_type == "Obj" or self.ret_type == "Nothing") :
                raise TypeError(f'Function {self.method_name} returns Nothing but defined with something incompatible ')

        # Save the variable scope for this method for code generation
        self.method_scope_local_var_dict = method_scope_local_var_dict
        local_var_dict = method_scope_local_var_dict.copy()

        return None

    def init_check(self, local_var_list: List[str], in_constructor: bool):
        formal_args, statement_block = self.children
        # formal arguments doesn't need init_check

        method_scope_local_var_list = local_var_list.copy()

        # Add arguments to local_var_list
        for method_parameter_name in formal_args.arg_names:
            method_scope_local_var_list.append(method_parameter_name)

        statement_block.init_check(method_scope_local_var_list, in_constructor)
        self.method_scope_local_var_list = method_scope_local_var_list.copy()
        return None


    def pretty_label(self) -> str:
        return f"ClassMethod Node: {self.method_name} returns {self.ret_type}"



class FormalArgsNode(ASTNode):
    """Formal args Node"""
    def __init__(self, lst: List[str]):
        super().__init__()
        self.arg_names = lst[::2]
        self.arg_types = lst[1::2]

    def r_eval(self, local_var_dict: Dict[str, str]):
        return None

    def type_eval(self, local_var_dict: Dict[str, str]):
        for arg_type in self.arg_types:
            if not ch.find_class(arg_type):
                raise ValueError(f'{arg_type} is an invalid type')
        return None

    def pretty_label(self) -> str:
        return f'Formal Args Node: {self.arg_names}'


class ProgramNode(ASTNode):
    """Program  Node"""
    def __init__(self, class_list: List[ASTNode], bare_statement_block: ASTNode):
        super().__init__()
        # self.children.append(program)
        self.children += class_list
        self.children.append(bare_statement_block)
        # self.num_classes = len(class_list)

    def r_eval(self, local_var_dict: Dict[str, str]):
        return ([subitem for child in self.children for subitem in child.r_eval(local_var_dict)])

    def type_eval(self, local_var_dict: Dict[str, str]):
        for child in self.children:
            child.type_eval(local_var_dict)
        return None

    def init_check(self, local_var_list: List[str], in_constructor: bool):
        for child in self.children:
            child.init_check(local_var_list, in_constructor)
        return None


    def pretty_label(self) -> str:
        return "ProgramNode"

# class MethodargsrecurNode(ASTNode):
#     """Methodargs recur Node"""
#     def __init__(self, methodargs: ASTNode, rexp: ASTNode):
#         super().__init__()
#         self.children.append(methodargs)
#         self.children.append(rexp)

#     def r_eval(self, local_var_dict: Dict[str, str]) -> List[str]:
#         methodargs, rexp = self.children
#         return (methodargs.r_eval(local_var_dict)
#                 + rexp.r_eval(local_var_dict))

#     def type_eval(self, local_var_dict: Dict[str, str]) -> None:
#         methodargs, rexp = self.children
#         methodargs.type_eval(local_var_dict)
#         rexp.type_eval(local_var_dict)
#         return None

#     def pretty_label(self) -> str:
#         return "MethodargsRecurNode"


class MethodargsNode(ASTNode):
    """Methodargs  Node"""
    def __init__(self, argument_list: ASTNode):
        super().__init__()
        self.children += argument_list
        # breakpoint()

    def r_eval(self, local_var_dict: Dict[str, str]):
        return [subitem for children in self.children for subitem in children.r_eval(local_var_dict)]

    def type_eval(self, local_var_dict: Dict[str, str]):
        return [child.type_eval(local_var_dict) for child in self.children]

    def pretty_label(self) -> str:
        return "MethodargsNode"

class BareStatementBlockNode(ASTNode):
    """BareStatementBloc Node"""
    def __init__(self, statement_list: ASTNode):
        super().__init__()
        self.children += statement_list

        self.bare_statement_block_local_var_dict = None
        self.bare_statement_block_local_var_list = None
        # breakpoint()

    def r_eval(self, local_var_dict: Dict[str, str]):
        ret = [subitem for children in self.children for subitem in children.r_eval(self.bare_statement_block_local_var_dict)]
        # Take care of potential returns in the bare statement. Replace with 0 because the bare statements have no arguments
        ret = [i.replace('TOFILL', str(0)) for i in ret]
        return ret

    def type_eval(self, local_var_dict: Dict[str, str]):
        # Populate variable with those initialized in this scope
        populate_local_var_dict_with_initialized_vars(local_var_dict, self.bare_statement_block_local_var_list)

        count = 1
        print(f'In BareStatementBlock type check iteration number: {count}')
        for child in self.children:
            child.type_eval(local_var_dict)
        print(local_var_dict)


        temp_local_var_dict = local_var_dict.copy()
        # Try additional passes through to make sure that variable types don't change
        while True:
            count += 1
            print(f'In BareStatementBlock type check iteration number: {count}')
            for child in self.children:
                child.type_eval(local_var_dict)
            print(local_var_dict)
            if temp_local_var_dict == local_var_dict:
                break
            else:
                print(f'BareStatementBlock type check additional pass detected type changes. Making another pass. Newly interpreted types {local_var_dict}')
                temp_local_var_dict = local_var_dict.copy()

        # Save the local_var_dict for the bare statement block for code generation
        self.bare_statement_block_local_var_dict = local_var_dict.copy()
        return None

    def init_check(self, local_var_list: List[str], in_constructor: bool):
        for child in self.children:
            child.init_check(local_var_list, in_constructor)

        self.bare_statement_block_local_var_list = local_var_list.copy()
        return None


    def pretty_label(self) -> str:
        return "BareStatementBlockNode"



class AssignmentNode(ASTNode):
    """Assignment Node"""
    def __init__(self, lexp: ASTNode, var_type: str, rexp: ASTNode):
        super().__init__()
        self.children.append(lexp)
        self.children.append(rexp)
        self.var_type = var_type

    def r_eval(self, local_var_dict: Dict[str, str]):
        lexp, rexp = self.children
        return (rexp.r_eval(local_var_dict)
                + lexp.l_eval())

    def type_eval(self, local_var_dict: Dict[str, str]):
        lexp, rexp = self.children

        actual_type = rexp.type_eval(local_var_dict)
        declared_type = self.var_type
        if lexp.get_value() in local_var_dict:
            prev_inferred_type = local_var_dict[lexp.get_value()]
        else:
            raise SyntaxError(f"Assignment to {lexp.get_value()} is invalid. Most likely, there is a path that doesn't initialize this variable")

        newly_inferred_type = None

        # If we are trying to assign a variable to something that doesn't return anything...
        if not actual_type:
            raise TypeError("Can't assign a variable to something a function that doesn't return anything")
        # if lexp.get_value() == 'y':
        #     breakpoint()

        # If we inferred a type before ...
        if prev_inferred_type:
            new_candidate_type = ch.find_LCA(prev_inferred_type, actual_type)
            local_var_dict[lexp.get_value()] = new_candidate_type
            newly_inferred_type = new_candidate_type
        else:
            local_var_dict[lexp.get_value()] = actual_type
            newly_inferred_type = actual_type

        # If a type was declared, make sure it is an actual class and make sure that it is legal with the newly inferred type. Then, honor the declared type over the acutal evalauated type
        if declared_type:
            if not ch.find_class(declared_type):
                raise TypeError(f'Declared type {declared_type} is an invalid class')
            if not ch.is_legal_assignment(declared_type, newly_inferred_type):
                raise TypeError(f'Assignment declared {declared_type} but inferred {newly_inferred_type}')
            local_var_dict[lexp.get_value()] = declared_type

        lexp.type_eval(local_var_dict)
        rexp.type_eval(local_var_dict)

        return None

    # def get_field_variables(self, field_var_dict: Dict[str, str], temp_local_var_dict: Dict[str, str]):
    #     lexp, rexp = self.children
    #     if isinstance(lexp, ThisReferenceLexpNode):
    #         field_var_dict[lexp.variable] = rexp.type_eval(temp_local_var_dict)

    def init_check(self, local_var_list: List[str], in_constructor: bool):
        lexp, rexp = self.children
        # First check if the right hand side is a valid statement, if so add the left to the local_var_list
        rexp.init_check(local_var_list, in_constructor)
        if lexp.get_value() not in local_var_list:
            local_var_list.append(lexp.get_value())

        # If there is an assignment to 'this.' (i.e. a class field) outside of the constructor report an error
        if not in_constructor and isinstance(lexp, ThisReferenceLexpNode):
            raise SyntaxError("Can't assign field variables outside the construcor statement block")

        return None


    def pretty_label(self) -> str:
        return f"AssignmentNode {self.var_type}"


class RexpNode(ASTNode):
    """Rexp Node"""
    def __init__(self, rexp: ASTNode):
        super().__init__()
        self.children.append(rexp)

    def r_eval(self, local_var_dict: Dict[str, str]) -> List[str]:
        # Bare right expression need a pop to get rid the thing it returns (whatever that is)
        return self.children[0].r_eval(local_var_dict)

    def c_eval(self, true_branch: str, false_branch: str, local_var_dict: Dict[str, str]) -> List[str]:
        return self.children[0].c_eval(true_branch, false_branch, local_var_dict)

    def type_eval(self, local_var_dict: Dict[str, str]) -> str:
        return self.children[0].type_eval(local_var_dict)

    def init_check(self, local_var_list: List[str], in_constructor: bool):
        self.children[0].init_check(local_var_list, in_constructor)
        return None

    def pretty_label(self) -> str:
        return "RexpNode"

class ConstructorCall(ASTNode):
    """Rexp Node"""
    def __init__(self, caller_name: str, constructor_arguments: ASTNode):
        super().__init__()
        self.children.append(constructor_arguments)
        self.caller_name = caller_name

    def r_eval(self, local_var_dict: Dict[str, str]):
        constructor_arguments = self.children[0]
        constructorargs_r_eval = constructor_arguments.r_eval(local_var_dict) if constructor_arguments else []
        return (constructorargs_r_eval +
                [f'\tnew {self.caller_name}'] +
                [f'\tcall {self.caller_name}:$constructor'])

    def c_eval(self, true_branch: str, false_branch: str, local_var_dict: Dict[str, str]) -> List[str]:
        # return self.children[0].c_eval(true_branch, false_branch, local_var_dict)
        return None

    def type_eval(self, local_var_dict: Dict[str, str]):
        methodargs = self.children[0]
        constructor_arguments_types = methodargs.type_eval(local_var_dict) if methodargs else []
        ch.is_legal_invocation(self.caller_name, '$constructor', constructor_arguments_types)

        return self.caller_name

    def init_check(self, local_var_list: List[str], in_constructor: bool):
        return None

    def pretty_label(self) -> str:
        return "ConstructorCallNode"



# class BareLexpNode(ASTNode):
#     """BareLexp Node"""
#     def __init__(self, lexp: str):
#         super().__init__()
#         self.value = lexp

#     def r_eval(self, local_var_dict: Dict[str, str]):
#         return self.value

#     def l_eval(self):
#         return [f'\tstore {self.value}']

#     def type_eval(self, local_var_dict: Dict[str, str]):
#         return local_var_dict[self.value]

#     def pretty_label(self) -> str:
#         return f"BareLexpNode {self.value}"

class ThisReferenceLexpNode(ASTNode):
    """ThisLexp Node"""
    def __init__(self, field_variable: str):
        super().__init__()
        self.variable = field_variable

    def r_eval(self, local_var_dict: Dict[str, str]):
        return ['\tload $', f'\tload_field $:{self.variable}']

    def l_eval(self):
        return ['\tload $', f'\tstore_field $:{self.variable}']

    def type_eval(self, local_var_dict: Dict[str, str]):
        # Assume that the initialization is done already here - init check must have passsed already
        return local_var_dict['this.' + self.variable]

    def init_check(self, local_var_list: List[str], in_constructor: bool):
        if 'this.' + self.variable not in local_var_list:
            raise ValueError(f"{'this.' + self.variable} is referenced before assignment")
        return None

    def get_value(self) -> str:
        return 'this.' + self.variable

    # def get_prev_defined_type(self, local_var_dict: Dict[str, str]):
    #     return local_var_dict.get('this.' + self.variable, None)

    def pretty_label(self) -> str:
        return f"ThisLexpNode {self.variable}"

class FieldReferenceLexpNode(ASTNode):
    """FieldLexp Node"""
    def __init__(self, atomic_expr: ASTNode, field_name: str):
        super().__init__()
        self.children.append(atomic_expr)
        self.field_name = field_name

    def r_eval(self, local_var_dict: Dict[str, str]):
        atomic_expr = self.children[0]
        atomic_expr_type = atomic_expr.type_eval(local_var_dict)
        return (atomic_expr.r_eval(local_var_dict) +
                [f'\tload_field {atomic_expr_type}:{self.field_name}'])

    def get_value(self) -> str:
        return self.value

    def type_eval(self, local_var_dict: Dict[str, str]):
        atomic_expr = self.children[0]
        atomic_expr_type = atomic_expr.type_eval(local_var_dict)

        # Find the class of the referred field
        referred_class = ch.find_class(atomic_expr_type)
        if self.field_name in referred_class.fields_list.keys():
            return referred_class.fields_list[self.field_name]
        else:
            raise ReferenceError(f'Field {self.field_name} is referenced for {atomic_expr_type} but it does not exist')

    def init_check(self, local_var_list: List[str], in_constructor: bool):
        return None


    def pretty_label(self) -> str:
        return f"FieldLexpNode {self.field_name}"


class VarReferenceNode(ASTNode):
    """VarReferecnce Node"""
    def __init__(self, variable: str):
        super().__init__()
        self.variable = variable

    def r_eval(self, local_var_dict: Dict[str, str]):
        return [f'\tload {self.variable}']

    def l_eval(self):
        return [f'\tstore {self.variable}']


    def get_value(self):
        return self.variable

    def type_eval(self, local_var_dict: Dict[str, str]) -> str:
        return local_var_dict[self.variable]

    def init_check(self, local_var_list: List[str], in_constructor: bool):
        if self.variable not in local_var_list:
            raise ValueError(f"{self.variable} is referenced before assignment")
        return None

    # def get_prev_defined_type(self, local_var_dict: Dict[str, str]):
    #     return local_var_dict.get(self.variable, None)

    def c_eval(self, true_branch: str, false_branch: str, local_var_dict: Dict[str, str]) -> List[str]:
        bool_code = self.r_eval(local_var_dict)
        return bool_code + [f"\tjump_if {true_branch}", f"\tjump {false_branch}"]

    def pretty_label(self) -> str:
        return f'VarReferenceNode: {self.variable}'


class ConstNode(ASTNode):
    """Constant"""
    def __init__(self, value: str, value_type: str):
        super().__init__()
        self.value = value
        self.value_type = value_type

    def r_eval(self, local_var_dict: Dict[str, str]):
        return [f"\tconst {self.value}"]

    def type_eval(self, local_var_dict: Dict[str, str]):
        return self.value_type

    def init_check(self, local_var_list: List[str], in_constructor: bool):
        return None

    def pretty_label(self) -> str:
        return f"ConstNode {self.value}"


class BoolNode(ASTNode):
    """Boolean """
    def __init__(self, value: str):
        super().__init__()
        self.value = value

    def r_eval(self, local_var_dict: Dict[str, str]) -> List[str]:
        return [f"\tconst {self.value}"]

    def c_eval(self, true_branch: str, false_branch: str, local_var_dict: Dict[str, str]):
        bool_code = self.r_eval(local_var_dict)
        return bool_code + [f"\tjump_if {true_branch}", f"\tjump {false_branch}"]

    def type_eval(self, local_var_dict: Dict[str, str]):
        return "Boolean"

    def init_check(self, local_var_list: List[str], in_constructor: bool):
        return None

    def pretty_label(self) -> str:
        return f"BoolNode {self.value}"



class ComparisonNode(ASTNode):
    """Comparisons are the leaves of conditional branches
    and can also return boolean values
    """
    def __init__(self, left: ASTNode, right: ASTNode, comp_op: str):
        super().__init__()
        self.children.append(left)
        self.children.append(right)
        self.comp_op = comp_op


    def r_eval(self, local_var_dict: Dict[str, str]):
        """Called if we want a boolean VALUE rather than a branch"""
        left, right = self.children
        left_code = left.r_eval(local_var_dict)
        right_code = right.r_eval(local_var_dict)
        caller_type = left.type_eval(local_var_dict)

        if self.comp_op == "==":
            return right_code + left_code + [f'\tcall {caller_type}:EQUALS']
        if self.comp_op == "<":
            return right_code + left_code + [f'\tcall {caller_type}:LESS']
        if self.comp_op == ">":
            return right_code + left_code + [f'\tcall {caller_type}:MORE']
        if self.comp_op == "<=":
            return right_code + left_code + [f'\tcall {caller_type}:ATMOST']
        if self.comp_op == ">=":
            return right_code + left_code + [f'\tcall {caller_type}:ATLEAST']

    def type_eval(self, local_var_dict: Dict[str, str]):
        left, right = self.children

        caller_type = left.type_eval(local_var_dict)
        right_type = right.type_eval(local_var_dict)
        quackClassEntry = ch.find_class(caller_type)

        # If equals, make sure that the equals exists
        if self.comp_op == "==":
            ch.is_legal_invocation(caller_type, 'EQUALS', [right_type])
        if self.comp_op == "<":
            ch.is_legal_invocation(caller_type, 'LESS', [right_type])
        if self.comp_op == ">":
            ch.is_legal_invocation(caller_type, 'MORE', [right_type])
        if self.comp_op == "<=":
            ch.is_legal_invocation(caller_type, 'ATMOST', [right_type])
        if self.comp_op == ">=":
            ch.is_legal_invocation(caller_type, 'ATLEAST', [right_type])
        return "Boolean"

    def init_check(self, local_var_list: List[str], in_constructor: bool):
        left, right = self.children
        left.init_check(local_var_list, in_constructor)
        right.init_check(local_var_list, in_constructor)
        return None

    def c_eval(self, true_branch: str, false_branch: str, local_var_dict: Dict[str, str]) -> List[str]:
        bool_code = self.r_eval(local_var_dict)
        return bool_code + [f"\tjump_if {true_branch}", f"\tjump {false_branch}"]

    def pretty_label(self) -> str:
        return f"ComparisonNode: {self.comp_op}"

class AndNode(ASTNode):
    """Boolean and, short circuit; can be evaluated for jump or for boolean value"""
    def __init__(self, left: ASTNode, right: ASTNode):
        super().__init__()
        self.children.append(left)
        self.children.append(right)

    # FIXME: Needs r_eval to allow production of boolean value

    def r_eval(self, local_var_dict: Dict[str, str]) -> List[str]:
        left, right = self.children
        return (left.r_eval(local_var_dict) + right.r_eval(local_var_dict) + ['\tcall Boolean:AND'])

    def c_eval(self, true_branch: str, false_branch: str, local_var_dict: Dict[str, str]):
        """Use in a conditional branch"""
        continue_label = new_label("and")
        left, right = self.children
        return (left.c_eval(continue_label, false_branch, local_var_dict)
                + [continue_label + ":"]
                + right.c_eval(true_branch, false_branch, local_var_dict)
                )

    def type_eval(self, local_var_dict: Dict[str, str]):
        return "Boolean"

    def init_check(self, local_var_list: List[str], in_constructor: bool):
        left, right = self.children
        left.init_check(local_var_list)
        right.init_check(local_var_list)
        return None

    def pretty_label(self) -> str:
        return "AndNode"


class OrNode(ASTNode):
    """Boolean or, short circuit; can be evaluated for jump or for boolean value"""
    def __init__(self, left: ASTNode, right: ASTNode):
        super().__init__()
        self.children.append(left)
        self.children.append(right)

    # FIXME: Needs r_eval to allow production of boolean value

    def r_eval(self, local_var_dict: Dict[str, str]):
        left, right = self.children
        return (left.r_eval(local_var_dict) + right.r_eval(local_var_dict) + ['\tcall Boolean:OR'])

    def c_eval(self, true_branch: str, false_branch: str, local_var_dict: Dict[str, str]) -> List[str]:
        """Use in a conditional branch"""
        continue_label = new_label("and")
        left, right = self.children
        return (left.c_eval(true_branch, continue_label, local_var_dict)
                + [continue_label + ":"]
                + right.c_eval(true_branch, false_branch, local_var_dict)
                )

    def type_eval(self, local_var_dict: Dict[str, str]):
        return "Boolean"

    def init_check(self, local_var_list: List[str], in_constructor: bool):
        left, right = self.children
        left.init_check(local_var_list)
        right.init_check(local_var_list)
        return None

    def pretty_label(self) -> str:
        return "OrNode"


class NotNode(ASTNode):
    """Boolean or, short circuit; can be evaluated for jump or for boolean value"""
    def __init__(self, statement: ASTNode):
        super().__init__()
        self.children.append(statement)

    # FIXME: Needs r_eval to allow production of boolean value

    def r_eval(self, local_var_dict: Dict[str, str]):
        statement = self.children[0]
        return (statement.r_eval(local_var_dict) + ['\tcall Boolean:NOT'])

    def c_eval(self, true_branch: str, false_branch: str, local_var_dict: Dict[str, str]) -> List[str]:
        """Use in a conditional branch"""
        statement = self.children[0]
        return statement.c_eval(false_branch, true_branch, local_var_dict)

    def type_eval(self, local_var_dict: Dict[str, str]):
        return "Boolean"

    def init_check(self, local_var_list: List[str], in_constructor: bool):
        statement = self.children[0]
        statement.init_check(local_var_list, in_constructor)
        return None

    def pretty_label(self) -> str:
        return "NotNode"


class IsInstanceNode(ASTNode):
    """IsInstance Node"""
    def __init__(self, rexp: ASTNode, target_class: str):
        super().__init__()
        self.children.append(rexp)
        self.target_class = target_class

    def r_eval(self, local_var_dict: Dict[str, str]):
        target_variable = self.children[0]
        return target_variable.r_eval(local_var_dict)

    def c_eval(self, true_branch: str, false_branch: str, local_var_dict: Dict[str, str]):
        # Hacky but ¯\_(ツ)_/¯
        ret = self.children[0].c_eval(true_branch, false_branch, local_var_dict)
        ret.insert(ret.index('\tjump_if ' + true_branch), f'\tis_instance {self.target_class}')
        return ret

    def type_eval(self, local_var_dict: Dict[str, str]):
        target_variable = self.children[0]
        target_variable.type_eval(local_var_dict)
        return "Boolean"

    def init_check(self, local_var_list: List[str], in_constructor: bool):
        target_variable = self.children[0]
        target_variable.init_check(local_var_list, in_constructor)
        return None

    def pretty_label(self) -> str:
        return "IsInstance"

class TypeAlternativeNode(ASTNode):
    """Type alternative node"""
    def __init__(self, alt_name: str, type_name: str, StatementBlockNode: ASTNode):
        super().__init__()
        self.children.append(StatementBlockNode)
        self.alt_name = alt_name
        self.type_name = type_name

    def r_eval(self, local_var_dict: Dict[str, str]):
        return None

    def type_eval(self, local_var_dict: Dict[str, str]):
        return None

    def init_check(self, loacl_var_list: List[str], in_constructor: bool):
        return None

    def pretty_label(self) -> str:
        return f"TypeAlternativeNode: {self.alt_name}, {self.type_name}"



def parse_builtin_classes(builtinclass_json):
    global ch
    ch = class_hierarchy.parse_builtin_classes(builtinclass_json)

def print_class_hierarchy():
    global ch
    class_hierarchy.pretty_print(ch)
