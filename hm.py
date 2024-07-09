import re
import string
import streamlit as st
from antlr4 import *
from hmLexer import hmLexer
from hmParser import hmParser
from hmVisitor import hmVisitor
from graphviz import Digraph
from collections import deque

##############################################################################################################

class TreeVisitor(hmVisitor):

    def __init__(self):
        if 'symbol_table' not in st.session_state:
            st.session_state['symbol_table'] = {}
        self.symbol_table = st.session_state['symbol_table']
        self.type_counter = iter('abcdefghijklmnopqrstuvwxyz')
        self.assigned_types = {}
        self.symbol_table_2 = st.session_state['symbol_table_2'] = {}

    def visitNumero(self, ctx):
        node = SemanticNumberNode(int(ctx.NUM().getText()))
        return node

    def visitVariable(self, ctx):
        node = SemanticVariableNode(ctx.VAR().getText())
        return node

    def visitOperadors(self, ctx):
        node = SemanticOperatorNode(ctx.getText())
        return node

    def visitLambda(self, ctx):
        param = SemanticVariableNode(ctx.VAR().getText())
        body = self.visit(ctx.expr())
        node = SemanticLambdaNode(param, body)
        return node

    def visitApp(self, ctx):
        function = self.visit(ctx.expr(0))
        argument = self.visit(ctx.expr(1))
        node = SemanticApplicationNode(function, argument)
        return node

    def visitParentesisi(self, ctx):
        expression = self.visit(ctx.expr())
        node = SemanticParenNode(expression)
        return node
    
    def visitTypeAnnotation(self, ctx):
        expr = self.visit(ctx.expr())
        expr_repr = self.get_expr_representation(expr)
        type_ = self.visit(ctx.type_())
        self.symbol_table[expr_repr] = type_
        return expr
    
    def visitType(self, ctx):
        if len(ctx.type_()) == 1:
            return self.visit(ctx.type_(0))
        else:
            result_type = self.visit(ctx.type_(0))
            for i in range(1, len(ctx.type_())):
                result_type = f'({result_type} -> {self.visit(ctx.type_(i))})'
            return result_type

    
    def visitTypeArrow(self, ctx):
        left = self.visit(ctx.type_(0))
        right = self.visit(ctx.type_(1))
        return f'({right} -> {left})'
    
    
    def visitTypeN(self, ctx):
        return ctx.getText()
    
    def get_expr_representation(self, expr):
        if isinstance(expr, SemanticNumberNode):
            return str(expr.value)
        elif isinstance(expr, SemanticVariableNode):
            return expr.name
        elif isinstance(expr, SemanticOperatorNode):
            return expr.operator
        else:
            return repr(expr)

    def assign_types(self, root):
        queue = deque([root])
        while queue:
            node = queue.popleft()
            expr_repr = self.get_expr_representation(node)
            if expr_repr in self.symbol_table:
                node.type = self.symbol_table[expr_repr]
            elif expr_repr in self.assigned_types:
                node.type = self.assigned_types[expr_repr]
            else:
                node.type = next(self.type_counter)
                self.assigned_types[expr_repr] = node.type
            if isinstance(node, SemanticLambdaNode):
                queue.append(node.param)
                queue.append(node.body)
            elif isinstance(node, SemanticApplicationNode):
                queue.append(node.function)
                queue.append(node.argument)
            elif isinstance(node, SemanticParenNode):
                queue.append(node.expression)
    
    
    def divide(self, type):
        type = type.replace("(", "").replace(")", "")
        if "->" in type:
            parts = type.split("->")
            middle = len(parts) // 2
            part1 = "->".join(parts[:middle])
            part2 = "->".join(parts[middle:])
            return part1, part2 
        else:
            return type, type
    
    def subtract_types(self, type1, type2):
        
        # Remove parentheses from type1
        type1 = type1.replace("(", "").replace(")", "")
        # Split the type1 string by the delimiter '->'
        parts = re.split(r'\s*->\s*', type1)
        # Check if the first part matches type2
        if parts[0] == type2:
            # Return the remaining parts joined by '->'
            return "(" + "->".join(parts[1:]) + ")"
        else:
            # Raise a TypeError if type2 does not match the first part
            raise TypeError(f"{type1} vs {type2}")
    
    def abstraction(self, node):
        if (node.type in self.symbol_table_2):
            node.type = self.symbol_table_2[node.type]
        else:
            raise TypeError(f"Abstraction Error")
        
    def inference(self, node):
        if isinstance(node, SemanticApplicationNode) :
            self.inference(node.function)
            self.inference(node.argument)
            if(node.argument.type in string.ascii_lowercase):
                aux1,aux2 = self.divide(node.function.type)
                self.symbol_table_2[node.type] = aux1
                self.symbol_table_2[node.argument.type] = aux2
                node.type = aux1
                node.argument.type = aux2
            else :
                aux = self.subtract_types(node.function.type,node.argument.type)
                self.symbol_table_2[node.type] = aux
                node.type = aux
        if isinstance(node, SemanticParenNode) :
            self.inference(node.expression)
            self.symbol_table_2[node.type] = node.expression.type
            node.type = node.expression.type
        if isinstance(node, SemanticLambdaNode) :
            self.inference(node.body)
            self.abstraction(node.param)
            aux = "(" + "->".join([node.param.type, node.body.type]) + ")"
            self.symbol_table_2[node.type] = aux
            node.type = aux
            

#################################################################################################################

class SemanticNode:
    pass

class SemanticNumberNode(SemanticNode):
    def __init__(self, value):
        self.value = value
        self.type = None

    def __repr__(self):
        return f"SemanticNumberNode({self.value}, {self.type})"

class SemanticVariableNode(SemanticNode):
    def __init__(self, name):
        self.name = name
        self.type = None

    def __repr__(self):
        return f"SemanticVariableNode({self.name}, {self.type})"

class SemanticOperatorNode(SemanticNode):
    def __init__(self, operator):
        self.operator = operator
        self.type = None

    def __repr__(self):
        return f"SemanticOperatorNode({self.operator}, {self.type})"

class SemanticLambdaNode(SemanticNode):
    def __init__(self, param, body):
        self.param = param
        self.body = body
        self.type = None

    def __repr__(self):
        return f"SemanticLambdaNode({self.param}, {self.body}, {self.type})"

class SemanticApplicationNode(SemanticNode):
    def __init__(self, function, argument):
        self.function = function
        self.argument = argument
        self.type = None

    def __repr__(self):
        return f"SemanticApplicationNode({self.function}, {self.argument}, {self.type})"

class SemanticParenNode(SemanticNode):
    def __init__(self, expression):
        self.expression = expression
        self.type = None

    def __repr__(self):
        return f"SemanticParenNode({self.expression}, {self.type})"


#######################################################################################################################

def create_dot(node, dot=None, parent=None, edge_label=""):
    if dot is None:
        dot = Digraph()

    node_id = str(id(node))
    if isinstance(node, SemanticNumberNode):
        label = f"{node.value} \n {node.type}"
    elif isinstance(node, SemanticVariableNode):
        label = f"{node.name} \n {node.type}"
    elif isinstance(node, SemanticOperatorNode):
        label = f"{node.operator} \n {node.type}"
    elif isinstance(node, SemanticLambdaNode):
        label = f"λ \n {node.type}"
        create_dot(node.param, dot, node_id, "")
        create_dot(node.body, dot, node_id, "")
    elif isinstance(node, SemanticApplicationNode):
        label = f"@ \n {node.type}"
        create_dot(node.function, dot, node_id, "")
        create_dot(node.argument, dot, node_id, "")
    elif isinstance(node, SemanticParenNode):
        label = f"ParenExpr \n {node.type}"
        create_dot(node.expression, dot, node_id, "")
    else:
        label = f"Unknown \n {node.type}"

    dot.node(node_id, label)
    if parent:
        dot.edge(parent, node_id, label=edge_label)
    
    return dot

####################################################################################################################################################

def create_symbol_table(symbol_table):
    import pandas as pd
    df = pd.DataFrame(list(symbol_table.items()), columns=["Symbol", "Type"])
    return df

#####################################################################################################################################################


st.title("Comprovador de expresions Haskell")
tin = st.text_input("Expresio: ")
if(st.button("fer")) :
    
    input_stream = InputStream(tin)
    lexer = hmLexer(input_stream)
    token_stream = CommonTokenStream(lexer)
    parser = hmParser(token_stream)
    tree = parser.root()


    if parser.getNumberOfSyntaxErrors() == 0:
        visitor = TreeVisitor()
        semantic_tree = visitor.visit(tree)
        visitor.assign_types(semantic_tree)  # Assign types after visiting the entire tree
        
        dot = create_dot(semantic_tree)
        st.graphviz_chart(dot.source)

        symbol_table_df = create_symbol_table(visitor.symbol_table)
        symbol_table_dfinverted = symbol_table_df.iloc[::-1]
        st.write(symbol_table_dfinverted)

        visitor.inference(semantic_tree)
        dot = create_dot(semantic_tree)
        st.graphviz_chart(dot.source)

        symbol_table_df_2 = create_symbol_table(visitor.symbol_table_2)
        symbol_table_df_2_inverted = symbol_table_df_2.iloc[::-1]
        st.write(symbol_table_df_2_inverted)
        

    else:   
        st.write(parser.getNumberOfSyntaxErrors(), "Errors de sintaxi")
        print(tree.toStringTree(recog=parser))
