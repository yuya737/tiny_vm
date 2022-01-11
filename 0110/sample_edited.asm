# Sample assembly code
# (augment as the assember and loader are built out)
.class Sample:Obj

.method $constructor
    const 4
    const 2
    const 3
    call Int:times
    call Int:plus
    call Int:print
    pop
    halt

