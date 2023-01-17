# ZK-PDA

## WIP WARNING
This project is only a proof of concept, and was intended to be
exploratory in nature, use at your own risk!

## About ZK-PDA
zk-pda is a Pushdown Automata (PDA) to Circom transpiler written
in Python. The transpiler takes in a Python object-based description of a
PDA and converts it into a Circom circuit that takes an input
string and outputs whether the PDA accepts the string or not.

## Inspiration
This project is part of our work at Hack Lodge W23, inspired by the 
regex parser transpiler from the existing project
[zk-email-verify](https://github.com/zk-email-verify/zk-email-verify),
found under the directory `regex_to_circom`.

We wrote this project to improve our JSON parsing code in
[zkJSON](https://github.com/amirgamil/zkjson).
Since JSON is not a regular language, regex is not powerful enough
to describe all JSON strings, so we could not
just use the existing regex parser (if we want to be pedantic,
neither does our PDA, _technically_, due to finite memory lol).
The key difference is that we had to include a stack in our Circom,
which came with its own challenges.

Still WIP to migrate our old JSON parser to use this transpiler.

## Example Usage
The following is a PDA describing the language of balanced parentheses `(` and `)`, along with
a few examples of such strings.

| Example String  |  Is Balanced?  |
| --------------- | -------------- |
| `((()))`         | ✅             |
| `()()()()`       | ✅             |
| `(()`            | ❌             |
| `((((((`         | ❌             |
| `(()()(()))`     | ✅             |

```python
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
```

To generate an output circom circuit, we can call
the following to print the circuit to stdout.
```python
paren_circuit = circuit.CircomPdaCircuit(paren_pda)
print(paren_circuit.generate_main())
```
The resulting circuit will be have signature
`template PDA(strLength, stackDepth)`
with input `str[strLength]` and output `out`.
The input `str[strLength]` is an ASCII-encoded array, and
output `out` is `1` if and only if the string
is accepted, `0` otherwise.

The resulting circuit references templates from
`pda.circom`, which can be found in this repo, so make
sure to include it too when compiling!

The full source can be found in `json_pda.py`.

## Limitations
Epsilon transitions are not supported; this is especially hard to
accomplish in Circom. We have not looked into this yet,
but this probably means we can't fully parse all context-free languages yet.

## TODO
- [ ] Constraining multi-character groups
- [ ] Detecting stack overflows
- [ ] Look into epsilon transitions

## Contributors
Ethan
