# Instructions (03/14/22)

The parser/code generation components lives in `main/*py`. `AST_classes.py` defines all the node in the AST and their behavior, `class_hierarchy.py` defines the class heirarchy and related functions and `lark_parser.py` acts as the driver.

`quackc` and `quack` are provided to compile `*qk` files and takes a single argument. Consider some `S.qk` that defines classes `A,B,C` and a statement block at the end. `quackc` will generate `A.asm, B.asm, C.asm` and `S_main.asm` before calling `assemble.py` to compile them to `OBJ/A.json, OBJ/B.json, OBJ/C.json` and `OBJ/S_main.json`. 

The only thing (as far as I'm aware) that the this compiler requires is that classes are declared before referenced. For example `class Cat() extends Animal` needs to come after `class Animal()`.

The behavior of `quack` amounts to calling `quackc` and then calling the tiny_vm on the `*_main` function
