.class Main:Obj

.method $constructor
.local i,j,s,t
	const 40
	const 14
	call Int:plus
	store i
	const 9
	load i
	call Int:divide
	store j
	load j
	call Int:print
	load j
	call Int:string
	store s
	const "is cool\n"
	load s
	call String:plus
	store t
	load t
	call String:print
	halt
	return 0
