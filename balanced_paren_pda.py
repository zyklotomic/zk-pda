from circom_pda import pda, circuit
from circom_pda.pda import (
	State,
	InputSymbol,
	StackSymbol,
	StateTransition,
	StackAction,
	Pda,
)

s0 = State(0)
s1 = State(1)
open_paren = InputSymbol("(")
close_paren = InputSymbol(")")

stk_dollar = StackSymbol("$")
stk_one = StackSymbol("1")

transitions = [
	StateTransition(
		s0, s1, open_paren,
		StackAction(pda.eps, stk_dollar)
	),
	StateTransition(
		s1, s1, open_paren,
		StackAction(pda.eps, stk_one)
	),
	StateTransition(
		s1, s1, close_paren,
		StackAction(stk_one, pda.eps)
	),
	StateTransition(
		s1, s0, close_paren,
		StackAction(stk_dollar, pda.eps)
	)
]

# PDA in Circom for balanced parenthesis
accept_states = [s0]
paren_pda = Pda(transitions, s0, accept_states)
paren_circuit = circuit.CircomPdaCircuit(json_pda)
print(paren_circuit.generate_main())
