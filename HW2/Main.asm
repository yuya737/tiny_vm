.class Main:Obj

.method $constructor
.local x,y,z
	const 5
	store x
	load x
	const 4
	call Int:plus
	store y
	const "df"
	store z
	load y
	const 7
	call Int:plus
	call Int:print
	load z
	call String:print
	pop
	halt
