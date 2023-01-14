from dataclasses import dataclass
from collections import Counter, defaultdict
 
@dataclass(eq=False)
class StackSymbol:
    inner: str

@dataclass(eq=False)
class Epsilon:
    """Singleton to denote eps transitions and stack actions"""
    inner: str

eps = Epsilon("ε")

@dataclass
class StackAction:
    """Class for denoting stack transition"""
    stack_start: StackSymbol | Epsilon
    stack_end: StackSymbol | Epsilon

 
@dataclass(eq=False)
class InputSymbol:
    inner: str

@dataclass(eq=False)
class State:
    inner: any

@dataclass
class StateTransition:
    start_state: State
    end_state: State
    expected_symbol: InputSymbol
    stack_action: StackAction  
 

class Pda:  

    def __init__(self, transitions, init_state, accept_states):
        self._transitions = transitions
        self.init_state = init_state
        self.state_to_id = {}
        self.input_symbol_to_id = {}
        self.stack_symbol_to_id = {}
        self.state_to_id = {}

        # dst -> transition with end state == dst
        self.transition_map = defaultdict(list)
        self.accept_states = accept_states

        # self.failed_state = State("FAILED")
        # self.state_to_id[self.failed_state] = 0

        for t in transitions:
            # id 0 is RESERVED!!!!! for unknown input symbol,
            # failed state
            # and default stack symbol value
            if t.start_state not in self.state_to_id:
                self.state_to_id[t.start_state] = len(self.state_to_id) + 1 

            if t.end_state not in self.state_to_id:
                self.state_to_id[t.end_state] = len(self.state_to_id) + 1

            if t.expected_symbol not in self.input_symbol_to_id:
                self.input_symbol_to_id[t.expected_symbol] = 1 + len(self.input_symbol_to_id)

            if t.stack_action.stack_start not in self.stack_symbol_to_id:
                self.stack_symbol_to_id[t.stack_action.stack_start] = \
                    1 + len(self.stack_symbol_to_id)

            if t.stack_action.stack_end not in self.stack_symbol_to_id:
                self.stack_symbol_to_id[t.stack_action.stack_end] = \
                    1 + len(self.stack_symbol_to_id) 

            self.transition_map[t.end_state].append(t)

        # for t in transitions:
        #     if t.start_state not in self.state_to_id:
        #         self.state_to_id[t.start_state] = len(self.state_to_id)
        #     if t.end_state not in self.state_to_id:
        #         self.state_to_id[t.end_state] = len(self.state_to_id)
        #     if t.input_symbol not in self.input_symbol_to_id:
        #         self.input_symbol_to_id[t.input_symbol] = len(self.input_symbol_to_id)
        #     if t.stack_symbol not in self.stack_symbol_to_id:
        #         self.stack_symbol_to_id[t.stack_symbol] = len(self.stack_symbol_to_id)

        #     self.transition_map[t.end_state].append(t)
        #     self.states.add(t.start_state)
        #     self.states.add(t.end_state)
 
	
