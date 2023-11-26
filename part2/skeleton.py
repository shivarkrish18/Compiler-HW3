import ast
import argparse
import z3

# Some example functions on how to use the python ast module:

# Given a python file, return an AST using the python ast module.
def get_ast_from_file(fname):
    f = open(fname, 'r')
    s = f.read()
    f.close()
    module_ast = ast.parse(s)
    body_ast = module_ast.body[0]    
    return body_ast

# Example of how to get information for the ast FOR_node
def get_loop_constraints(FOR_node):
    loop_var = FOR_node.target.id
    lower_bound = pp_expr(FOR_node.iter.args[0])
    upper_bound = pp_expr(FOR_node.iter.args[1])

    # return the for loop information in some structure
    # return (loop_var, lower_bound, upper_bound)

# Check if an ast node is a for loop
def is_FOR_node(node):
    return str(node.__class__) == "<class '_ast.For'>"

# Top level function. Given a python file name, it parses the file,
# and analyzes it to determine if the top level for loop can be done
# in parallel.
#
# It returns True if it is safe to do the top loop in parallel,
# otherwise it returns False.
def analyze_file(fname):
    body_ast = get_ast_from_file(fname)

    # Assuming the top level structure is a For loop
    for_loop = body_ast.body[0] if is_FOR_node(body_ast.body[0]) else None
    if for_loop is None:
        raise ValueError('No top-level for loop found')

    loop_var, lower_bound, upper_bound = get_loop_constraints(for_loop)
    accesses = {'read': set(), 'write': set()}

    # Get all read/write accesses within the loop body
    for node in for_loop.body:
        get_accesses(node, accesses, write=isinstance(node, ast.Assign))

    # Suggested steps:
    # 1. Get loop constraints (variables and bounds)
    # 2. Get expressions for read_index and write_index
    # 3. Create constraints and check them using Z3
    
    # Example of setting up Z3 solver
    solver = Solver()
    loop_var_z3 = Int(loop_var)
    lower_bound_z3 = int(lower_bound) # This needs to be parsed correctly
    upper_bound_z3 = int(upper_bound) # This needs to be parsed correctly

    # Add loop bounds constraint
    solver.add(loop_var_z3 >= lower_bound_z3, loop_var_z3 < upper_bound_z3)

    # Constraints for reads and writes
    # For each read and write, create Z3 variables and add constraints
    # that express the read and write operations.
    # For example:
    # write_expr = ...
    # read_expr = ...
    # solver.add(write_expr == read_expr)

    # Check for conflicts
    # WW conflict
    ww_conflict = False
    if len(accesses['write']) > 1:
        # Add constraints to solver to check if any two writes can happen at the same iteration
        ww_conflict = True if solver.check() == sat else False

    # RW conflict
    rw_conflict = False
    if accesses['read'] & accesses['write']:
        # Add constraints to solver to check if any read can happen at the same time as a write
        rw_conflict = True if solver.check() == sat else False

    return ww_conflict, rw_conflict

    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()   
    parser.add_argument('pythonfile', help ='The python file to be analyzed') 
    args = parser.parse_args()
    ww_conflict, rw_conflict = analyze_file(args.pythonfile)
    print("Does the code have a write-write conflict? ", ww_conflict)
    print("Does the code have a read-write conflict?  ", rw_conflict)
