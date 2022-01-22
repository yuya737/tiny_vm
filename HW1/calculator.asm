.class Calculator:Obj

.method $constructor
	const 6
	const 0
	const 1
	call Int:minus
	call Int:times
	const 3
	const 0
	const 1
	call Int:minus
	call Int:times
	const 1
	call Int:plus
	call Int:divide
	const 3
	const 4
	call Int:minus
	call Int:times
	call Int:print
	pop
	halt
