.class Sample:Obj

.method $constructor
.local x,y
    const 4
    store x
    load x
    const 3
    call Int:equals
    jump_if done
    const "In if\n"
    call String:print
    jump done

done: const "Exit if\n"
    call String:print
    return 0
