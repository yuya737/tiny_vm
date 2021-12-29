/*
 * The built-in classes of Quack
 * (incomplete implementation)
 *
 */
#include <stdio.h>
#include <stdlib.h>  /* Malloc lives here   */
#include <string.h>  /* For strcpy */

#include "builtins.h"
#include "vm_core.h"
#include "vm_state.h"
#include "vm_ops.h"
#include <assert.h>

/* Dynamic type check (isinstance).
 * Like an assertion:  Either passes and does nothing,
 * or halts execution with an error.
 */
void assert_is_type(obj_ref thing, class_ref expected) {
    if (thing->header.tag != GOOD_OBJ_TAG) {
        fprintf(stderr, "Type check failure: %p is Not on object!\n", thing);
        assert(0);
    }
    class_ref thing_class = thing->header.clazz;
    class_ref clazz = thing_class;
    while (clazz) {
        if (clazz == expected) {
            return; // OK
        }
        if (clazz == the_class_Obj) {
            break;
         }
        clazz = clazz->header.super;
    }
    fprintf(stderr,
            "Type check failure:%s is not subclass of %s\n",
            thing_class->header.class_name,
            expected->header.class_name);
    assert(0);
}

/* Trampolines and shims:
 * We must make it possible for the interpreter to call native methods,
 * and for native methods to call both native and interpreted methods,
 * without knowing in advance which it is calling!
 */

/* Methods that haven't been implemented yet. */
obj_ref native_tbd() {
    obj_ref this = vm_fp->obj;
    class_ref clazz = this->header.clazz;
    char *class_name = clazz->header.class_name;
    printf("Unimplemented method on %s\n", class_name);
    return nothing;
}

/* Since the method needs to know its arity, we have a TBD
 * (unimplemented) method for each each arity 0..2.
 */
vm_Word method_tbd_0[] = {
        {.instr = vm_op_enter},
        {.instr = vm_op_call_native},
        {.native = native_tbd},
        {.instr = vm_op_return},
        {.intval = 0}
};

vm_Word method_tbd_1[] = {
        {.instr = vm_op_enter},
        {.instr = vm_op_call_native},
        {.native = native_tbd},
        {.instr = vm_op_return},
        {.intval = 1}
};

vm_Word method_tbd_2[] = {
        {.instr = vm_op_enter},
        {.instr = vm_op_call_native},
        {.native = native_tbd},
        {.instr = vm_op_return},
        {.intval = 2}
};

/* Built-in native methods may
 * construct custom string representations.
 */
obj_ref new_string(char *s);

/* ==============
 * Obj
 * Fields: None
 * Methods:
 *    Constructor  (called after allocation)
 *    STRING
 *    PRINT
 *    EQUALS
 *
 * ==============
 */

/* Constructor */
obj_ref new_Obj(  ) {
    obj_ref new_thing = (obj_ref) malloc(sizeof(struct obj_struct));
    new_thing->header.clazz = the_class_Obj;
    new_thing->header.tag = GOOD_OBJ_TAG;
    return new_thing;
}

/* Obj:STRING
 * Creates "<Object at 0xAAAA>" where AAAA is address of this
 */
obj_ref Obj_method_STRING(obj_ref this) {
    assert_is_type(this, the_class_Obj);  // Probably can't fail
    char *rep;
    asprintf(&rep, "<Object at 0x%ld>", (long) this);
    obj_ref str = new_string(rep);
    return str;
}


vm_Word method_Obj_print[] = {
        {.instr = vm_op_enter},
        {.instr = vm_op_load},
        {.intval = 0},
        {.instr = vm_op_methodcall},
        {.intval = 1},  // string method
        {.instr = vm_op_methodcall},
        {.intval = 2},  // print method of class string
        {.instr = vm_op_return},
        {.intval = 0}
};

///* Obj:EQUALS (Note we may want to replace this */
//obj_ref Obj_method_EQUALS(obj_ref this) {
//    obj_ref other = vm_eval_pop();
//    if (this == other) {
//        return lit_true;
//    } else {
//        return lit_false;
//    }
//}
//
/* The Obj Class (a singleton) */
struct  class_struct  the_class_Obj_struct = {
        .header = {"object",
                   0,
                   sizeof(struct obj_Obj_struct) },
        .vtable =
                {method_tbd_0, // constructor
                 method_tbd_0, // STRING
                 method_Obj_print, // PRINT
                 method_tbd_1  // EQUALS
                }
};

const class_ref the_class_Obj = &the_class_Obj_struct;

/* ================
 * String
 * Fields:
 *    One hidden field, currently holding char*
 * Methods:
 *    Those of Obj, plus ordering, concatenation
 *    Constructor  (called after allocation)
 *    STRING
 *    PRINT
 *    EQUALS
 *    FIXME: (Incomplete for now.)
 * ==================
 */


/* Construct a string object containing
 * a particular value  (aka "boxed",
 * like Int in Java, not like int in Java).
 * Used by built-in vm methods, not
 * available directly to the interpreted program.
 */
obj_ref new_string(char *s) {
    obj_String boxed = (obj_String) vm_new_obj(the_class_String);
    boxed->text = s;
    return (obj_ref) boxed;
}

/* String literals constructor,
 * used by compiler and not otherwise available in
 * Quack programs.
 */
int str_literal_const(char *s_lit) {
    int const_index = lookup_const_index(s_lit);
    if (const_index) {
        return const_index;
    }
    obj_ref boxed = new_string(s_lit);
    const_index = create_const_value(s_lit, boxed);
    return const_index;
}

/* Constructor */
obj_ref native_String_constructor(void ) {
    obj_ref this = vm_fp->obj;
    assert_is_type(this, the_class_String);
    obj_String this_str = (obj_String) this;
    this_str->text = "";
    return this;
}

vm_Word method_String_constructor[] = {
        {.instr = vm_op_enter},
        {.instr = vm_op_call_native},
        {.native = native_String_constructor},
        {.instr = vm_op_return},
        {.intval = 0}
};

/* String:STRING (returns itself) */
vm_Word method_String_string[] = {
        {.instr = vm_op_enter},
        {.instr = vm_op_load},
        {.intval = 0}, // The "this" object at fp
        {.instr = vm_op_return},
        {.intval = 0 }
};

/* String:PRINT */
obj_ref native_String_print() {
    obj_ref this = vm_fp->obj;
    /* Checked downcast */
    assert_is_type(this, the_class_String);
    struct obj_String_struct* this_string = (struct obj_String_struct*)  this;
    /* Then we can access fields */
    fprintf(stdout, "PRINT |%s|\n", this_string->text); //FIXME
    return nothing;
}

vm_Word method_String_print[] = {
        {.instr = vm_op_enter},
        {.instr = vm_op_call_native},
        {.native = native_String_print },
        {.instr = vm_op_return},
        {.intval = 0 }
};


/* String:EQUALS (Note we may want to replace this */
obj_ref String_method_EQUALS(obj_ref this) {
    obj_ref other = vm_eval_pop();
    /* But is it really? */
    if (other->header.clazz != the_class_String) {
        return lit_false;
    }
    obj_String this_str = (obj_String) this;
    obj_String other_str = (obj_String) other;
    if (strcmp(this_str->text,other_str->text) == 0) {
        return lit_true;
    } else {
        return lit_false;
    }
}

/* The String Class (a singleton) */
struct  class_struct  the_class_String_struct = {
        .header = {.class_name="String",
                   .super=the_class_Obj},
        method_String_constructor,     /* Constructor */
        method_String_string,
        method_String_print,
        method_tbd_1
};

class_ref the_class_String = &the_class_String_struct;


/* ================
 * Boolean
 * Fields:
 *    One hidden field, an int (0 for False, -1 for True)
 * Methods:
 *    Those of Obj
 * =================
 */

/* Boolean:STRING */
obj_ref Boolean_method_STRING(obj_ref this) {
    if (this == lit_true) {
        return get_const_value(str_literal_const("true"));
    } else if (this == lit_false) {
        return get_const_value(str_literal_const("false"));
    } else {
        return get_const_value(str_literal_const("!!!BOGUS BOOLEAN"));
    }
}

/* Inherit Obj:EQUAL, since we have only two
 * objects of class Boolean.
 */

/* Inherit Obj:PRINT, which will call Boolean:STRING */

/* The Boolean Class (a singleton) */
struct  class_struct  the_class_Boolean_struct = {
        .header = {"Boolean",
                   the_class_Obj,
                   sizeof(struct obj_Boolean_struct) },
        .vtable =
                {
                 method_tbd_0, // constructor
                 method_tbd_0, // STRING
                 method_tbd_0, // PRINT
                 method_tbd_1  // EQUALS
                }
};

class_ref the_class_Boolean = &the_class_Boolean_struct;

/*
 * These are the only two objects of type Boolean that
 * should ever exist. The constructor just picks one of
 * them.
 */
struct obj_Boolean_struct lit_false_struct =
        { .header.clazz = &the_class_Boolean_struct,
          .value = 0 };
obj_ref lit_false = (obj_ref) &lit_false_struct;
struct obj_Boolean_struct lit_true_struct =
        { .header.clazz = &the_class_Boolean_struct,
          .value =-1 };
obj_ref lit_true = (obj_ref) &lit_true_struct;

/* ==============
 * Nothing (really just a singleton Obj)
 * Fields: None
 * Methods:
 *    Constructor  (called after allocation)
 *    STRING
 *    PRINT
 *    EQUALS
 *
 * ==============
 */
/*  Constructor */

/* Boolean:STRING */


/* Inherit Obj:EQUAL, since we have only one
 * object of class None
 */

/* Inherit Obj:PRINT, which will call Nothing:STRING */

/* The Nothing Class (a singleton) */
struct  class_struct  the_class_Nothing_struct = {
        .header = {"Nothing",
                   the_class_Obj,
                   sizeof(struct class_Nothing_struct) },
        .vtable =
                {method_tbd_0, // constructor
                 method_tbd_0, // STRING
                 method_tbd_0, // PRINT
                 method_tbd_1  // EQUALS
                }
};

class_ref the_class_Nothing = &the_class_Nothing_struct;

/*
 * This is the only instance of class Nothing that
 * should ever exist
 */
static struct obj_Nothing_struct nothing_struct =
        { .header.clazz = &the_class_Nothing_struct,
          .header.tag = GOOD_OBJ_TAG
        };
obj_ref nothing = (obj_ref) &nothing_struct;

/* ================
 * Int
 * Fields:
 *    One hidden field, an int
 * Methods:
 *    Those of Obj
 *    PLUS
 *    LESS
 *    (add more later)
 * =================
 */

/* Constructor */

/* If you create a new Int object, it is
 * initialized to zero.  Note that the return value of the
 * native function is pushed onto the stack to be returned
 * from the interpreted constructor method.  We return "this"
 * so that allocation and initialization leave the constructed
 * object on the stack.
 */
obj_ref native_int_constructor(void ) {
    obj_ref this = vm_fp->obj;
    assert_is_type(this, the_class_Int);
    obj_Int this_int = (obj_Int) this;
    this_int->value = 0;
    return this;
}

vm_Word method_int_constructor[] = {
        {.instr = vm_op_enter},
        {.instr = vm_op_call_native},
        {.native = native_int_constructor},
        {.instr = vm_op_return},
        {.intval = 0}
};

/* Int:STRING */

obj_ref native_Int_string(void ) {
    obj_ref this = vm_fp->obj;
    assert_is_type(this, the_class_Int);
    obj_Int this_int = (obj_Int) this;
    char *s;
    asprintf(&s, "%d", this_int->value);
    obj_ref string_rep = new_string(s);
    return string_rep;
}

vm_Word method_Int_string[] = {
        {.instr = vm_op_enter},
        {.instr = vm_op_call_native},
        {.native = native_Int_string},
        {.instr = vm_op_return},
        {.intval = 0}
};


/* Int:EQUALS */
obj_ref Int_method_EQUALS(obj_Int this, obj_Obj other) {
    obj_Int other_int = (obj_Int) other;
    /* But is it? */
    if (other_int->header.clazz != this->header.clazz) {
        return lit_false;
    }
    if (this->value != other_int->value) {
        return lit_false;
    }
    return lit_true;
}

/* Inherit Obj:PRINT, which will call Int:STRING */

/* STUB (fixme): special native for printing int. */

obj_ref native_int_print(void ) {
    obj_ref this = vm_fp->obj;
    assert_is_type(this, the_class_Int);
    obj_Int this_int = (obj_Int) this;
    printf("Printing integer value: %d\n", this_int->value);
    return nothing;
}


vm_Word OLD_method_int_print[] = {
        {.instr = vm_op_enter},
        {.instr = vm_op_call_native},
        {.native = native_int_print},
        {.instr = vm_op_return},
        {.intval = 0}
};

/* LESS (new native_method) */
obj_ref Int_method_LESS(obj_Int this, obj_Int other) {
    if (this->value < other->value) {
        return lit_true;
    }
    return lit_false;
}


/* PLUS (new native_method) */
obj_ref native_int_plus(void ) {
    obj_ref this = vm_fp->obj;
    assert_is_type(this, the_class_Int);
    obj_Int this_int = (obj_Int) this;
    obj_ref other = (vm_fp - 1)->obj;
    assert_is_type(other, the_class_Int);
    obj_Int other_int = (obj_Int) other;
    printf("Adding integer values: %d + %d\n",
           this_int->value, other_int->value);
    obj_ref sum = new_int(this_int->value + other_int->value);
    return sum;
}

vm_Word method_int_plus[] = {
        {.instr = vm_op_enter},
        {.instr = vm_op_call_native},
        {.native = native_int_plus},
        {.instr = vm_op_return},
        {.intval = 1}
};

/* The Int Class (a singleton) */
struct  class_struct  the_class_Int_struct = {
        .header = {
                .class_name = "Int",
                .super = the_class_Obj,
                .object_size = sizeof(struct obj_Int_struct),
        },
        .vtable = {
                method_int_constructor,  // constructor
                method_Int_string, // STRING
                method_Obj_print, // PRINT
                method_tbd_1,  // EQUALS
                method_tbd_1, // LESS
                method_int_plus
        }
 };

class_ref the_class_Int = &the_class_Int_struct;

/* Construct an integer object containing
 * a particular value  (aka "boxed",
 * like Int in Java, not like int in Java).
 * Used by built-in vm methods like Int:add, not
 * available directly to the interpreted program.
 */
obj_ref new_int(int n) {
    obj_Int boxed = (obj_Int) vm_new_obj(the_class_Int);
    boxed->value = n;
    return (obj_ref) boxed;
}

/* Integer literals constructor,
 * used by compiler and not otherwise available in
 * Quack programs.  Returns the *index* of the constant,
 * e.g., int_literal(42) could return 3!
 * new_int may be called by other built-in methods,
 * e.g., Int.add.
 */
int int_literal_const(char *n_lit) {
    int const_index = lookup_const_index(n_lit);
    if (const_index) {
        return const_index;
    }
    int as_int = atoi(n_lit);
    obj_ref boxed = new_int(as_int);
    const_index = create_const_value(n_lit, boxed);
    return const_index;
}

