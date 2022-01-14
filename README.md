# Instructions for HW1 - tiny calculator (01/14/22)

The lark parser lives at `HW1/lark_parser.py` and takes as argument the path to the desired `.asm` file. I have used `python HW1/lark_parser.py HW1/calculator.asm`. It will prompt for user input where an arithmetic expression can be inputted

`run_calc.sh` will call `assemble.py`, piping it to `sample.json` and then the `build/tiny_vm` execuatable. 
