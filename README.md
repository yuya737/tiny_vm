# Instructions for HW2 - Nano Quack (01/28/22)

The lark parser lives at `HW2/lark_parser.py` and takes as argument an input quack expression and the path to the desired `.asm` file and . I have used `python lark_parser.py test_input Main.asm` - ran inside `HW2/`. (The sample input from class is under `HW2/test_input`).

Once the `Main.asm` is built, calling `python assemble.py HW2/Main.asm OBJ/Main.json; ./bin/tiny_vm -L OBJ Main` from the main directory will compile the assembly code, and run it
