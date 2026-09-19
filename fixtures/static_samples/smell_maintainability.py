# Smells: Deep nesting, dead code, long method, parameter bloat
def deeply_nested_and_dead_code(a, b, c, d, e, f):
    if a > 0:
        for i in range(b):
            while c > 0:
                if d > 0:
                    for k in range(e):
                        print("deep")
    return 42
    print("This is dead code")
