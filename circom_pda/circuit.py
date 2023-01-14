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
            f"  component cmp[{num_symbs}];",
        ]

        # symbol 0 is reserved for unrecognized symbol!!!!!
        res.append(f"  component oneHotDecoder = OneHotDecoder({num_symbs+1});")
        res.append("")
        for symbol, i in self.pda.input_symbol_to_id.items():
            num_symbols = len(symbol.inner)
            if num_symbols == 1:
                res.append(f"  // matching '{symbol.inner}'")
                res.append(f"  component cmp[{i}] = IsEqual();")
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
            "template strSymbolTypes(strLen) {",
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

        start_st = state_transition.start_state.n
        end_st = state_transition.end_state.n

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
            res.append(
                f"    stateTrans[i][{end_state.n}] = "
                f" StateTransitionCombinator({cnt}, stackDepth);"
            )
        return res

    def generate_all_state_transitions(self):
        res = []
        for end_state, transitions in self.pda.transition_map.items():
            res.append(f"    // transitions to state {end_state.n}")
            for i, t in enumerate(transitions): 
                res.extend(self.generate_state_transition(t, i))
                res.append("")
 
        return res

    def generate_pda_accept_check(self):
        num_accept_states = len(self.pda.accept_states)
        if num_accept_states == 1:
            res = [
                f"  out <== states[strLength][{self.pda.accept_states[0].n}];"
            ]
        else:
            res = [
                f"  component acceptCheck = MultiOR({num_accept_states});"
            ]
            for i, acc_state in enumerate(self.pda.accept_states):
                res.append(f"  acceptCheck.in[i] <== states[strLength][{acc_state.n}];")
            res.append("  out <== acceptCheck.out;")

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
        num_states = len(self.pda.states)
        pda_template = [
            "template PDA(strLength, stackDepth) {",
            "\n".join(self.generate_symbol_id_comments()),
            "  signal input str[strLength];",
            "  signal output out; // 0 for rej, 1 for accept",
            "",
            "  signal stack[strLength+1][stackDepth];",
            f"  signal states[strLength+1][{num_states}];",
            "",
            "  states[0][0] <== 1;",
            "  states[0][1] <== 0;",
            "",
            "  for (var i=0; i<stackDepth; i++) stack[0][i] <== 0;",
            "",
            f"  component stateTrans[strLength][{num_states}]",
            "  component stateDecoder[strLength];",
            "  component tokenType = allSymbolTypes(strLength);",
            "  tokenType.in <== str;",
            "  component stackCombinator[strLength];",
            "",
            "  for (var i=0; i<strLength; i++) {",
            f"    stateDecoder[i] = OneHotDecoder({num_states})",
            f"    for(var k=0; k<{num_states}; k++) stateDecoder[i].in[k] <== states[i][k];",
            f"    var currentTokenType = tokenType.out[i]",
            f"    var currentState = stateDecoder[i].out;",
            "",
            "\n".join(self.generate_state_transitions_init()),
            "",
            "    // current state-specific args",
            f"    for(var k=0; k<{num_states}; k++) " + "{",
            "      stateTrans[i][k].stack <== stack[i];",
            "      stateTrans[i][k].currentState <= currentState",
            "      stateTrans[i][k].currentTokenType <== currentTokenType;",
            "    }",
            "",
            "\n".join(self.generate_all_state_transitions()),
            "",
            f"    stackCombinator[i] = StackCombinator({num_states}, stackDepth);",
            f"    for (var k=0; k<{num_states}; k++) " + "{",
            f"      states[i+1][k] <== stateTrans[i][k].shouldTransition;",
            "       stackCombinator[i].stack[k] <== stateTrans[i][k].newStack;",
            "    }",
            "    stack[i+1] <== stackCombinator[i].stackSum;",
            "  }",
            "\n".join(self.generate_pda_accept_check()),
            "}"
        ]


        return pda_template


