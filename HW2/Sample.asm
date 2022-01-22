.class Sample:Obj

.method $constructor
.local x
    enter
    const 4
    store x
    load $
    load x
    call Int:print
    pop 
    return 0
