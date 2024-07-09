grammar hm;

// Regles

root: expr
    ;  

expr: NUM                               #numero
    | VAR                               #variable
    | ('(+)' | '(-)')                   #operadors
    | expr expr                         #app
    | '\\' VAR '->' expr                #lambda
    | '(' expr ')'                      #parentesisi
    | expr '::' type                    #typeAnnotation
    ;

type: T                               #typeN
    | type '->' type                    #typeArrow
    ;

T: ('A'..'Z');
NUM: ('0'..'9')+;
VAR: ('a'..'z')+;

// Regles lèxiques
WS: [ \t\r\n]+ -> skip;
