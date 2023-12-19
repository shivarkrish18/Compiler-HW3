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
'''def get_loop_constraints(FOR_node):
    loop_var = FOR_node.target.id
    lower_bound = pp_expr(FOR_node.iter.args[0])
    upper_bound = pp_expr(FOR_node.iter.args[1])

    # return the for loop information in some structure
    # return (loop_var, lower_bound, upper_bound)'''


# Check if an ast node is a for loop
def is_FOR_node(node):
    return str(node.__class__) == "<class '_ast.For'>"

# Top level function. Given a python file name, it parses the file,
# and analyzes it to determine if the top level for loop can be done
# in parallel.
#
# It returns True if it is safe to do the top loop in parallel,
# otherwise it returns False.

def pp_expr(node, variables, thread_id):
    node_type = type(node)
    if node_type is ast.Constant:
        return node.value
    elif node_type is ast.Name:
        return variables[node.id][thread_id]
    elif node_type is ast.BinOp:
        left, right = pp_expr(node.left, variables, thread_id), pp_expr(node.right, variables, thread_id)
        operator_type = type(node.op)
        operations = { ast.Add: lambda x, y: x + y, ast.Sub: lambda x, y: x - y, ast.Mult: lambda x, y: x * y, ast.Div: lambda x, y: x / y, ast.Mod: lambda x, y: x % y}
        return operations[operator_type](left, right)
    
def analyze_file(fname):
    ast_node = get_ast_from_file(fname)

    # Suggested steps:
    # 1. Get loop constraints (variables and bounds)
    # 2. Get expressions for read_index and write_index
    # 3. Create constraints and check them

    # Set these variables to True if there is a write-write (ww)
    # conflict or a read-write (rw) conflict


    ww_conflict, rw_conflict = False, False

    #Implementation starts here
    solver = z3.Solver()

    #Maintain a dictionary for variables in AST
    variables = {}
    outer_loop_var = ast_node.target.id

    #Traverse through the tree
    while ast_node:
        node_type = type(ast_node)
        #If it is a For loop, get the lower and upper bound 
        #Create two integers with a condition that they should be within the bounds
        if node_type is ast.For:
            loop_var = ast_node.target.id
            lower_bound, upper_bound = ast_node.iter.args
            next_node = ast_node.body[0]

            variables[loop_var] = z3.Ints(f"{loop_var}_0 {loop_var}_1")

            for thread_id in (0, 1):
                solver.add(variables[loop_var][thread_id] >= pp_expr(lower_bound, variables, thread_id),
                           variables[loop_var][thread_id] < pp_expr(upper_bound, variables, thread_id))
                
            ast_node = next_node

        #If it is the assignment expression, then store ww and rw conditions
        elif node_type is ast.Assign:
            write_expression = ast_node.targets[0].slice
            read_expression = ast_node.value.slice

            write_write_condition = pp_expr(write_expression, variables, 0) == pp_expr(write_expression, variables, 1)
            read_write_condition = pp_expr(read_expression, variables, 0) == pp_expr(write_expression, variables, 1)

            solver.add(variables[outer_loop_var][0] != variables[outer_loop_var][1])            
            solver.push()
            solver.add(write_write_condition)
            ww_conflict = solver.check().r == 1
            solver.pop()
            solver.add(read_write_condition)
            rw_conflict = solver.check().r == 1
            break

    return ww_conflict, rw_conflict
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()   
    parser.add_argument('pythonfile', help ='The python file to be analyzed') 
    args = parser.parse_args()
    ww_conflict, rw_conflict = analyze_file(args.pythonfile)
    print("Does the code have a write-write conflict? ", ww_conflict)
    print("Does the code have a read-write conflict?  ", rw_conflict)