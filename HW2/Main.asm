.class Main:Obj

.method $constructor
.local i,j,cat,other
	const 13
	const 42
	call Int:plus
	store i
	const 32
	load i
	call Int:minus
	store j
	load j
	call Int:print
	const "Nora"
	store cat
	const "can solve puzzles"
	store other
	load other
	load cat
	call String:plus
	call String:print
	const "\n"
	call String:print
	halt
	return 0
