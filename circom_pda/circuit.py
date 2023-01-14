from . import pda

POP_STACK = 0
PUSH_STACK = 1 
POP_PUSH_STACK = 2
NO_OP_STACK = 3


class CircomPdaCircuit:

    def __init__(self, pda):
        self.pda = pda

    def generate_symbol_lookup(self):
        num_symbs = len(self.pda.input_symbol_to_id)
        res = [
            "template getSymbolType() {"
            "",
            "  signal input in;",
            "  signal output out;",
            "",
            f"  component cmp[{num_symbs+1}];",
        ]

        # symbol 0 is reserved for unrecognized symbol!!!!!
        res.append(f"  component oneHotDecoder = OneHotDecoder({num_symbs+1});")
        res.append("")
        res.append(f"  oneHotDecoder.in[0] <== 0;")
        for symbol, i in self.pda.input_symbol_to_id.items():
            num_symbols = len(symbol.inner)
            if num_symbols == 1:
                res.append(f"  // matching '{symbol.inner}'")
                res.append(f"  cmp[{i}] = IsEqual();")
                res.append(f"  cmp[{i}].in[0] <== in;")
                res.append(f"  cmp[{i}].in[1] <== {ord(symbol.inner)};")
            else:
                res.append(f"  // matching {list(symbol.inner)}")
                res.append(f"  component cmp[{i}] = MultiOR({num_symbols});")
                for ch in symbol.inner:
                    res.append(f"  cmp[{i}] <-- (in == {ord(ch)}) ? 1 : 0;")
                    res.append(f"  cmp[{i}] * (in - {ord(ch)})) === 0;") 

            res.append(f"  oneHotDecoder.in[{i}] <== cmp[{i}].out;")
            res.append("")

        res.append("  out <== oneHotDecoder.out;")
        res.append("}")

        return res

    def generate_all_symbol_types(self):
        return [
            "template allSymbolTypes(strLen) {",
            "   signal input in[strLen];",
            "   signal output out[strLen];",
            "",
            "   component cmp[strLen];",
            "   for (var i=0; i<strLen; i++) {",
            "       cmp[i] = getSymbolType();",
            "       cmp[i].in <== in[i];",
            "   }",
            "",
            "   for (var i=0; i<strLen; i++) {",
            "     out[i] <== cmp[i].out;",
            "   }",
            "}" 
        ]


    def generate_state_transition(self, state_transition, ix):
        # ix is used to denote the ix-th state transition
        # into the same end state, for circom code gen

        start_st = self.pda.state_to_id[state_transition.start_state]
        end_st = self.pda.state_to_id[state_transition.end_state]

        _exp_sym = state_transition.expected_symbol
        exp_sym = self.pda.input_symbol_to_id[_exp_sym]

        _sa = state_transition.stack_action
        t = (_sa.stack_start, _sa.stack_end)
        if t == (pda.eps, pda.eps):
            stk_act = NO_OP_STACK
            exp_stk_top = -1 # unused
            ign_stk = 1
            stk_inp = -1 # unused
        elif t[0] == pda.eps:
            stk_act = PUSH_STACK
            exp_stk_top = -1 # unused
            ign_stk = 1
            stk_inp = self.pda.stack_symbol_to_id[t[1]]
        elif t[1] == pda.eps:
            stk_act = POP_STACK
            exp_stk_top = self.pda.stack_symbol_to_id[t[0]]
            ign_stk = 0
            stk_inp = -1 # unused
        else:
            stk_act = POP_PUSH_STACK
            exp_stk_top = self.pda.stack_symbol_to_id[t[0]]
            ign_stk = 0
            stk_inp = self.pda.stack_symbol_to_id[t[1]]

        # TODO: Comment state transitions

        return [
            f"    // {_exp_sym.inner}, {_sa.stack_start.inner} -> {_sa.stack_end.inner}",
            f"    stateTrans[i][{end_st}].expectedStackTop[{ix}] <== {exp_stk_top};",
            f"    stateTrans[i][{end_st}].ignoreStack[{ix}] <== {ign_stk};",
            f"    stateTrans[i][{end_st}].expectedState[{ix}] <== {start_st};",
            f"    stateTrans[i][{end_st}].expectedTokenType[{ix}] <== {exp_sym};", 
            f"    stateTrans[i][{end_st}].stackAction[{ix}] <== {stk_act};",
            f"    stateTrans[i][{end_st}].stackInput[{ix}] <== {stk_inp};"
        ]

    def generate_state_transitions_init(self):
        res = []
        for end_state in self.pda.transition_map:
            cnt = len(self.pda.transition_map[end_state])
            state_id = self.pda.state_to_id[end_state]
            res.append(
                f"    stateTrans[i][{state_id}] = "
                f" StateTransitionCombinator({cnt}, stackDepth);"
            )
        return res

    def generate_all_state_transitions(self):
        res = []
        for end_state, transitions in self.pda.transition_map.items():
            state_id = self.pda.state_to_id[end_state]
            res.append(f"    // transitions to state {state_id}")
            for i, t in enumerate(transitions): 
                res.extend(self.generate_state_transition(t, i))
                res.append("")
 
        return res

    def generate_pda_accept_check(self):
        num_accept_states = len(self.pda.accept_states)
        if num_accept_states == 1:
            state_id = self.pda.state_to_id[self.pda.accept_states[0]]
            res = [
                f"  out <== states[strLength][{state_id}];"
            ]
        else:
            res = [
                f"  component acceptCheck = MultiOR({num_accept_states});"
            ]
            for i, acc_state in enumerate(self.pda.accept_states):
                res.append(f"  acceptCheck.in[{i}] <== states[strLength][{acc_state.n}];")
            res.append("  out <== acceptCheck.out;")

        return res

    def generate_state_init(self):
        init_state_id = self.pda.state_to_id[self.pda.init_state]

        res = [
            "  states[0][0] <== 0;",
            f"  states[0][{init_state_id}] <== 1;"
        ]

        for i in range(1, len(self.pda.state_to_id)+1):
            if i != init_state_id:
                res.append(f"  states[0][{i}] <== 0;");

        return res

    def generate_symbol_id_comments(self):
        comments = []
 
        comments.append("  // Stack Symbol IDs (ignore epsilon)")
        for stack_symb, sym_id in self.pda.stack_symbol_to_id.items():
            if len(stack_symb.inner) == 1:
                comments.append(f"  // {stack_symb.inner} -> {sym_id}")
            else:
                comments.append(f" // {list(stack_symb.inner)} -> {sym_id}")

        comments.append("")
        comments.append("  // Input Symbol IDs")
        for input_symb, sym_id in self.pda.input_symbol_to_id.items():
            comments.append(f"  // {input_symb.inner} -> {sym_id}")

        return comments
                

    def generate_pda(self):
        num_states = len(self.pda.state_to_id)
        # we do num_states+1 because state 0 is reserved for fail state
        pda_template = [
            "template PDA(strLength, stackDepth) {",
            "\n".join(self.generate_symbol_id_comments()),
            "  signal input str[strLength];",
            "  signal output out; // 0 for rej, 1 for accept",
            "",
            "  signal stack[strLength+1][stackDepth];",
            f"  signal states[strLength+1][{num_states+1}];",
            "",
            "\n".join(self.generate_state_init()),
            "",
            "  for (var i=0; i<stackDepth; i++) stack[0][i] <== 0;",
            "",
            f"  component stateTrans[strLength][{num_states+1}];",
            "  component stateDecoder[strLength];",
            "  component tokenType = allSymbolTypes(strLength);",
            "  tokenType.in <== str;",
            "  component stackCombinator[strLength];",
            "",
            "  for (var i=0; i<strLength; i++) {",
            f"    stateDecoder[i] = OneHotDecoder({num_states+1});",
            f"    stateDecoder[i].in[0] <== 0;",
            f"    for (var k=1; k<{num_states+1}; k++) stateDecoder[i].in[k] <== states[i][k];",
            f"    var currentTokenType = tokenType.out[i];",
            f"    var currentState = stateDecoder[i].out;",
            "",
            "\n".join(self.generate_state_transitions_init()),
            "",
            "    // current state-specific args",
            f"    for(var k=1; k<{num_states+1}; k++) " + "{",
            "      stateTrans[i][k].stack <== stack[i];",
            "      stateTrans[i][k].currentState <== currentState;",
            "      stateTrans[i][k].currentTokenType <== currentTokenType;",
            "    }",
            "",
            "\n".join(self.generate_all_state_transitions()),
            "",
            f"    stackCombinator[i] = StackCombinator({num_states+1}, stackDepth);",
            "    for (var d=0; d<stackDepth; d++) {"
            "      stackCombinator[i].stack[0][d] <== 0;",
            "    }"
            f"    for (var k=1; k<{num_states+1}; k++) " + "{",
            f"      states[i+1][k] <== stateTrans[i][k].shouldTransition;",
            "      stackCombinator[i].stack[k] <== stateTrans[i][k].newStack;",
            "    }",
            "    stack[i+1] <== stackCombinator[i].stackSum;",
            "  }",
            "\n".join(self.generate_pda_accept_check()),
            "}"
        ] 

        return pda_template

    def generate_main(self):
        pragma_imports = "\n".join([
            "pragma circom 2.0.8;",
            "",
            'include "./node_modules/circomlib/circuits/comparators.circom";',
            'include "./node_modules/circomlib/circuits/gates.circom";',
            'include "./pda.circom";',
        ])

        get_symbol_type = "\n".join(self.generate_symbol_lookup())
        all_symbol_types = "\n".join(self.generate_all_symbol_types())

        pda = "\n".join(self.generate_pda())

        return "\n".join([
            pragma_imports,
            "",
            get_symbol_type,
            "",
            all_symbol_types,
            "",
            pda
        ])
        


