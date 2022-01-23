.class Sample:Obj

.method $constructor
.local x,y
	const "SF"
	store x
	load x
	store y
	load y
	call String:print
	pop
	halt
