pragma circom 2.1.2;

include "./node_modules/circomlib/circuits/comparators.circom";
include "./node_modules/circomlib/circuits/gates.circom";

template MultiOR(N) {
  signal input in[N];
  signal output out;

  component or[N-1];
  signal accum[N];
  accum[0] <== in[0];
  for (var i=1; i<N; i++) {
    or[i-1] = OR();
    or[i-1].a <== accum[i-1];
    or[i-1].b <== in[i];
    accum[i] <== or[i-1].out;
  }
  out <== accum[N-1];
}

template OneHotDecoder(n) {
    // zero-indexed!!!
    signal input in[n];
    signal output out;

    var res;
    for (var i=0; i<n; i++) res += i * in[i];
    out <== res;
}

template StackPop(stackDepth) {
  signal input stack[stackDepth];
  signal output newStack[stackDepth];

  for (var i=0; i<stackDepth-1; i++) {
    newStack[i] <== stack[i+1];
  }
  newStack[stackDepth-1] <== 0;
}

template StackPush(stackDepth) {
  signal input stack[stackDepth];
  signal input a;
  signal output newStack[stackDepth];

  for (var i=1; i<stackDepth-1; i++) {
    newStack[i] <== stack[i-1];
  }
  newStack[0] <== a;
}

template StackPopPush(stackDepth) {
  signal input stack[stackDepth];
  signal input a;
  signal output newStack[stackDepth];

  for (var i=1; i<stackDepth; i++) {
    newStack[i] <== stack[i];
  }
  newStack[0] <== a;
}


template StateTransition(stackDepth) {
  signal input stack[stackDepth];
  signal input expectedStackTop;
  // signifies eps -> esp transition, ignores stack
  signal input ignoreStack;

  signal input currentState;
  signal input expectedState;

  signal input currentTokenType;
  signal input expectedTokenType;

  signal input stackAction;
  signal input stackInput;

  signal output shouldTransition;
  // newStack completely 0 if !shouldTransition
  signal output newStack[stackDepth];

  component eqStack = IsEqual();
  eqStack.in[0] <== stack[0];
  eqStack.in[1] <== expectedStackTop;

  component eqState = IsEqual();
  eqState.in[0] <== currentState;
  eqState.in[1] <== expectedState;

  component eqTokenType = IsEqual();
  eqTokenType.in[0] <== currentTokenType;
  eqTokenType.in[1] <== expectedTokenType;

  component orStack = OR();
  orStack.a <== eqStack.out;
  orStack.b <== ignoreStack;
  signal stackOK <== orStack.out;

  component and3 = MultiAND(3);
  and3.in[0] <== stackOK;
  and3.in[1] <== eqState.out;
  and3.in[2] <== eqTokenType.out;
  shouldTransition <== and3.out;

  component stackMux = StackMux(stackDepth);
  stackMux.stackAction <== stackAction;
  stackMux.stack <== stack;
  stackMux.stackInput <== stackInput;

  for (var i=0; i<stackDepth; i++) {
    newStack[i] <== shouldTransition * stackMux.newStack[i];
  }

}

// for when no states transitions to the destination state
// dang, if we had template generics that would be pog
//         AbstractStateTransition
//          /               \
//   DummyStateTrans.     StateTrans.
template DummyStateTransition(stackDepth) {
  signal input stack[stackDepth];
  signal input expectedStackTop;

  signal input currentState;
  signal input expectedState;

  signal input currentTokenType;
  signal input expectedTokenType;

  signal input stackAction;
  signal input stackInput;

  signal output shouldTransition;
  signal output newStack[stackDepth];

  shouldTransition <== 0;
  for (var i=0; i<stackDepth; i++) newStack[i] <== 0;
}

template StateTransitionCombinator(N, stackDepth) {
  signal input stack[stackDepth];
  signal input expectedStackTop[N];
  signal input ignoreStack[N];

  signal input currentState;
  signal input expectedState[N];

  signal input currentTokenType;
  signal input expectedTokenType[N];

  signal input stackAction[N];
  signal input stackInput[N];

  component stateTransition[N];
  for (var i=0; i<N; i++) {
    stateTransition[i] = StateTransition(stackDepth);
    stateTransition[i].stack <== stack;
    stateTransition[i].expectedStackTop <== expectedStackTop[i];
    stateTransition[i].ignoreStack <== ignoreStack[i];

    stateTransition[i].currentState <== currentState;
    stateTransition[i].expectedState <== expectedState[i];

    stateTransition[i].currentTokenType <== currentTokenType;
    stateTransition[i].expectedTokenType <== expectedTokenType[i];

    stateTransition[i].stackAction <== stackAction[i];
    stateTransition[i].stackInput <== stackInput[i];
  }

  signal output shouldTransition;
  // all 0's if !shouldTransition
  signal output newStack[stackDepth];

  component orN = MultiOR(N);
  for (var i=0; i<N; i++) {
    orN.in[i] <== stateTransition[i].shouldTransition;
  }
  shouldTransition <== orN.out;

  signal newStackVal[stackDepth][N];
  for (var j=0; j<stackDepth; j++) {
    newStackVal[j][0] <== shouldTransition * stateTransition[0].newStack[j];
    for (var i=1; i<N; i++) {
      var k = shouldTransition * stateTransition[i].newStack[j];
      newStackVal[j][i] <== newStackVal[j][i-1] + k;
    }
    newStack[j] <== newStackVal[j][N-1];
  }
}

template StackMux(stackDepth) {
  // 0 for pop, 1 for push, 2 for popPush, 3 for no-op
  signal input stackAction;
  signal input stack[stackDepth];
  signal input stackInput;
  signal output newStack[stackDepth];

  component eq[4];
  eq[0] = IsEqual();
  eq[1] = IsEqual();
  eq[2] = IsEqual();
  eq[3] = IsEqual();

  eq[0].in[0] <== 0;
  eq[1].in[0] <== 1;
  eq[2].in[0] <== 2;
  eq[3].in[0] <== 3;

  eq[0].in[1] <== stackAction;
  eq[1].in[1] <== stackAction;
  eq[2].in[1] <== stackAction;
  eq[3].in[1] <== stackAction;

  component popStack = StackPop(stackDepth);
  popStack.stack <== stack;

  component pushStack = StackPush(stackDepth);
  pushStack.stack <== stack;
  pushStack.a <== stackInput;

  component popPushStack = StackPopPush(stackDepth);
  popPushStack.stack <== stack;
  popPushStack.a <== stackInput;

  signal accumVal[stackDepth][3];
  for (var i=0; i<stackDepth; i++) {
    accumVal[i][0] <== eq[0].out * popStack.newStack[i];
    accumVal[i][1] <== accumVal[i][0] + eq[1].out * pushStack.newStack[i];
    accumVal[i][2] <== accumVal[i][1] + eq[2].out * popPushStack.newStack[i];
    newStack[i] <== accumVal[i][2] + eq[3].out * stack[i];
  }
}

template StackCombinator(M, stackDepth) {
  signal input stack[M][stackDepth];
  signal output stackSum[stackDepth];

  for (var i=0; i<stackDepth; i++) {
    var accum = 0;
    for (var j=0; j<M; j++) accum += stack[j][i];
    stackSum[i] <== accum;
  }
}
