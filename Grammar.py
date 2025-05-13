import random
from graphviz import Digraph
import pandas as pd

from FA import DFA
from Lexer import Token

EPS = "ε"
EOF = "$"


class Grammar:
    def __init__(self, T: list[str], NT: list[str], S: str, P: list[tuple[str, str]]):
        self.T = T
        self.NT = NT
        self.S = S
        self.P = P
        self.Pstr = [self.getPstr(A, beta) for A, beta in P]
        self.FirstSet = None
        self.FollowSet = None
        self.SelectSet = None
        self.LL1_TABLE = None
        self.CC = None
        self.CC_dict = None
        self.Action = None
        self.Goto = None

    def getPstr(self, A: str, beta: list):
        return A + " -> " + " ".join(beta)
    
    def getP(self, Pstr: str):
        return self.P[self.Pstr.index(Pstr)]

    @classmethod
    def load(cls, filename: str):
        with open(filename, "r") as f:
            T, NT, S, P = f.read().replace("eps", EPS).split("\n\n")
            NT = NT.split(" ")
            T = T.split(" ")
            P = [tuple(line.split(" -> ")) for line in P.split("\n")]
            P = [(A, beta.split()) for A, beta in P]
            return cls(T, NT, S, P)

    def firstSet(self) -> dict[str, set]:
        if self.FirstSet:
            return self.FirstSet
        first = {}
        for r in self.T + [EOF, EPS]:
            first[r] = {r}
        for r in self.NT:
            first[r] = set()
        fixed_point = True
        while fixed_point:
            is_changed = False
            for A, beta in self.P:
                rhs = set()
                allHasEPS = True
                for i in range(len(beta)):
                    rhs |= first[beta[i]] - {EPS}
                    if EPS not in first[beta[i]]:
                        allHasEPS = False
                        break
                if allHasEPS:
                    rhs.add(EPS)
                if not rhs <= first[A]:
                    first[A] |= rhs
                    is_changed = True
            fixed_point = is_changed
        self.FirstSet = first
        return self.FirstSet

    def get_first(self, beta: list) -> set:
        first = self.firstSet()
        rhs = set()
        allHasEPS = True
        for i in range(len(beta)):
            rhs |= first[beta[i]] - {EPS}
            if EPS not in first[beta[i]]:
                allHasEPS = False
                break
        if allHasEPS:
            rhs.add(EPS)
        return rhs

    def followSet(self) -> dict[str, set]:
        if self.FollowSet:
            return self.FollowSet

        first = self.firstSet()
        follow: dict[str, set] = {}
        for r in self.NT:
            follow[r] = set()
        follow[self.S] = {EOF}
        fixed_point = True
        while fixed_point:
            is_changed = False
            for A, beta in self.P:
                trailer = follow[A].copy()
                for i in range(len(beta) - 1, -1, -1):
                    if beta[i] in self.NT:
                        if not trailer <= follow[beta[i]]:
                            is_changed = True
                            follow[beta[i]] |= trailer
                        if EPS in first[beta[i]]:
                            trailer |= first[A] - {EPS}
                        else:
                            trailer = first[beta[i]]
                    else:
                        trailer = first[beta[i]].copy()
            fixed_point = is_changed
        self.FollowSet = follow
        return self.FollowSet

    def selectSet(self) -> dict[str, set]:
        if self.SelectSet:
            return self.SelectSet
        first = self.firstSet()
        follow = self.followSet()
        select = {}

        for A, beta in self.P:
            first_rule = self.get_first(beta)
            p = self.getPstr(A, beta)
            if EPS not in first_rule:
                select[p] = first_rule
            else:
                select[p] = first_rule | follow[A]
        return select

    def LL1_table(self) -> dict[str, dict[str, int]]:
        if self.LL1_TABLE:
            return self.LL1_TABLE
        select = self.selectSet()
        table = {}
        for i, (A, beta) in enumerate(self.P):
            table.setdefault(A, {})
            p = self.getPstr(A, beta)
            for w in select[p] - {EPS}:
                table[A][w] = i
            if EPS in select[p]:
                table[A][EOF] = i
        self.LL1_TABLE = table
        return table

    def isLL1(self):
        hasLeftRecursion = any(beta[0] == A for A, beta in self.P)
        if hasLeftRecursion:
            return False, "含有直接左递归，不是LL(1)文法"
        Aset = {A for A, beta in self.P}
        select = self.selectSet().items()
        for A in Aset:
            sets = [ s  for Pstr, s in select if  self.getP(Pstr)[0] == A]
            intersection = set()
            isIntersect = False
            for s in sets:
                for x in s:
                    if x in intersection:
                        isIntersect = True
                    else:
                        intersection.add(x)
            if isIntersect:
                return False, "存在回溯，不是LL(1)文法"
        return True, "是LL(1)文法"


    def LL1_analyze(self, token: Token) -> tuple[Digraph, list, str]:
        table = self.LL1_table()
        stack = [EOF, self.S]
        queue = []
        type, word = token.peek()
        error = False
        processList = []
        syntaxMsg = ""
        syntaxTree = {self.S: []}
        syntaxStack = [syntaxTree]
        queue.append(word)
        processList.append((stack.copy(), token.get_types(), "-"))

        while True:
            focus = stack[-1]
            node = syntaxStack[-1] if syntaxStack else {} 
            if focus == EOF and type == EOF:
                break
            elif focus in self.T or focus == EOF:
                if focus == type:
                    stack.pop()
                    syntaxStack.pop()
                    token.next()
                    type, word = token.peek()
                    queue.append(word)
                    processList.append((stack.copy(), token.get_types(), "→"))
                else:
                    exception_word = list(table[focus].keys())
                    syntaxMsg = f'{" ".join(queue)}\nsyntax error: excepted {" ".join(exception_word)} but gave {type}'
                    processList.append((stack.copy(), token.get_types(), "error"))
                    node[focus] = type + "error"
                    error = True
                    break
            elif focus in self.NT:
                idx = table[focus].get(type)
                if idx is not None:
                    stack.pop()
                    syntaxStack.pop()
                    stack.extend(reversed(self.P[idx][1]))
                    processList.append(([x for x in stack if x != EPS], token.get_types(), str(idx)))
                    for k in reversed(self.P[idx][1]):
                        t = k if k in self.T or k == EPS else {k: []}
                        node[focus].append(t)
                        syntaxStack.append(t)
                else:
                    exception_word = list(table[focus].keys())
                    syntaxMsg = f'{" ".join(queue)}\nsyntax error: excepted {" ".join(exception_word)} but gave {type}'
                    processList.append((stack.copy(), token.get_types(), "error"))
                    node[focus].append(type + "error")
                    error = True
                    break
            else:
                stack.pop()
                syntaxStack.pop()

        def reverse(node):
            if isinstance(node, str):
                return
            elif isinstance(node, list):
                node.reverse()
                for k in node:
                    reverse(k)
            else:
                for key in node:
                    reverse(node[key])

        reverse(syntaxTree)
        dot = self.buildSyntaxTreeDot(syntaxTree)
        if not error:
            return dot, processList, "success"
        else:
            return dot, processList, syntaxMsg

    def closure(self, s: list) -> list:
        worklist = s.copy()
        while worklist:
            A, beta, delta, a = worklist.pop(0)
            if not delta:
                continue
            C, *delta = delta
            if C in self.NT:
                for _, gamma in [p for p in self.P if p[0] == C]:
                    for b in self.get_first([*delta, a]):
                        item = (C, [], gamma, b)
                        if item not in s:
                            worklist.append(item)
                            s.append(item)
        return sorted(s)

    def goto(self, s: list, x: str) -> list:
        worklist = []
        for A, beta, delta, a in s:
            if delta and delta[0] == x:
                worklist.append((A, [*beta, delta[0]], delta[1:], a))
        return self.closure(worklist)

    def find_next(self, s: list) -> list:
        move = []
        for A, beta, delta, a in s:
            if delta and delta[0] not in move:
                move.append(delta[0])
        return list(filter(lambda x: x in move, self.T)) + list(filter(lambda x: x in move, self.NT))

    def build_CC(self) -> tuple[list[list], dict[str, dict[str, int]]]:
        if self.CC and self.CC_dict:
            return self.CC, self.CC_dict
        CC = [self.closure([(self.S, [], self.P[0][1], EOF)])]
        CC_dict = {}
        worklist = CC.copy()
        while worklist:
            s = worklist.pop(0)
            CC_dict[CC.index(s)] = {}
            for x in self.find_next(s):
                s1 = self.goto(s, x)
                if s1 not in CC:
                    worklist.append(s1)
                    CC.append(s1)
                CC_dict[CC.index(s)][x] = CC.index(s1)
        self.CC = CC
        self.CC_dict = CC_dict
        return self.CC, self.CC_dict

    def CCstr(self) -> list[str]:
        formatCC = lambda cc: ";".join(
            [f'[{A} -> {" ".join(beta)} * {" ".join(delta)}, {a}]' for A, beta, delta, a in cc]
        )
        CC, CC_dict = self.build_CC()
        CC_str = []
        CC_str.append(f"CC0={{{formatCC(CC[0])}}}")
        printed = set()
        for u, item in CC_dict.items():
            for w, v in item.items():
                if v not in printed:
                    printed.add(v)
                    CC_str.append(f"CC{v}=goto(CC{u},{w})={{{formatCC(CC[v])}}}")
        return CC_str

    def CC_DFA(self) -> DFA:
        CC, CC_dict = self.build_CC()
        cc_dfa = DFA(
            S=list(map(str, range(len(CC)))),
            sigma=self.T + self.NT + [EOF],
            delta=[(str(u), str(w), str(v)) for u, item in CC_dict.items() for w, v in item.items()],
            s0=str(0),
            A=[str(i) for i in range(len(CC)) if any(not delta for A, beta, delta, a in CC[i])],
        )
        return cc_dfa

    def LR1_table(self) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, str]]]:
        if self.Action and self.Goto:
            return self.Action, self.Goto
        CC, CC_dict = self.build_CC()
        Action = {}
        Goto = {}
        for u, item in CC_dict.items():
            Action.setdefault(u, {})
            Goto.setdefault(u, {})
            for w, v in item.items():
                if w in self.T:
                    if w in Action[u]:
                        raise Exception(f"Error: Action.at[{u}, {w}] = {Action[u][w]} but reassgin to {f's{v}'}")
                    Action[u][w] = f"s{v}"
                else:
                    Goto[u][w] = str(v)
        for u in range(len(CC)):
            for A, beta, delta, a in CC[u]:
                if not delta:
                    idx = self.Pstr.index(self.getPstr(A, beta))
                    if a in Action[u]:
                        raise Exception(f"Error: Action.at[{u}, {a}] = {Goto[u][a]} but reassgin to {f"r{idx}"}")
                    if (A, beta) == (self.S, self.P[0][1]):
                        Action[u][a] = "acc"
                    else:
                        Action[u][a] = f"r{idx}"
        self.Action = Action
        self.Goto = Goto
        return self.Action, self.Goto

    def LR1_analyze(self, token: Token)-> tuple[Digraph, list, str]:
        Action, Goto = self.LR1_table()
        stack = []
        queue = []
        stack.append((EOF, 0))
        type, word = token.next()
        queue.append(word)
        error = False
        processList = []
        syntaxMsg = ""
        syntaxTree = []
        while True:
            _, state = stack[-1]
            if type not in Action[state]:
                processList.append((state, type, stack.copy(), [], "error"))
                exception_word = [k for k, v in Action[state].items() if v != "-"]
                syntaxMsg = f'{" ".join(queue)}\nsyntax error: excepted {" ".join(exception_word)} but gave {type}'
                error = True
                break
            action = Action[state][type]
            if action.startswith("r"):
                A, beta = self.P[int(action[1:])]
                processList.append((state, type, [x[0] for x in stack], beta, action))
                subTree = []
                for i in range(len(beta)):
                    stack.pop()
                    subTree.insert(0, syntaxTree.pop())
                syntaxTree.append({A: subTree})
                newState = stack[-1][1]
                stack.append((A, int(Goto[newState][A])))
            elif action.startswith("s"):
                processList.append((state, type, [x[0] for x in stack], [], action))
                stack.append((type, int(action[1:])))
                syntaxTree.append(type)
                type, word = token.next()
                queue.append(word)
            elif action == "acc":
                syntaxTree = [{self.S: syntaxTree}]
                processList.append((state, type, [x[0] for x in stack], self.P[0][1], action))
                break
        dot = self.buildSyntaxTreeDot(syntaxTree)
        if not error:
            return dot, processList, "success"
        else:
            return dot, processList, syntaxMsg

    def buildSyntaxTreeDot(self, syntaxTree):
        dot = Digraph()
        idx = 0

        def dfs(node, fa):
            nonlocal idx
            if isinstance(node, str):
                cur = idx
                idx += 1
                dot.node(str(cur), node, shape="doublecircle")
                if fa is not None:
                    dot.edge(str(fa), str(cur))
            elif isinstance(node, list):
                for value in node:
                    dfs(value, fa)
            else:
                for key, value in node.items():
                    son = idx
                    idx += 1
                    dot.node(str(son), key, shape="circle")
                    if fa is not None:
                        dot.edge(str(fa), str(son))
                    dfs(value, son)

        dfs(syntaxTree, None)
        return dot

    def derivation(self, s: list[str]):
        print("".join(s))
        for i in range(len(s)):
            if s[i] in self.NT:
                self.derivation(s[:i] + random.choice(self.P[s[i]]) + s[i + 1 :])


if __name__ == "__main__":
    filename = "./input/Grammar/Expr_G.txt"
    G = Grammar.load(filename)
    if 'LL1' in filename:
        print("------------First------------")
        print(pd.Series(G.firstSet()))
        print("------------Follow------------")
        print(pd.Series(G.followSet()))
        print("------------Select------------")
        print(pd.Series(G.selectSet()))
        print("------------LL(1) Table------------")
        print(pd.Series(G.Pstr))
        print(pd.DataFrame(G.LL1_table(), index=G.T + [EOF], columns=G.NT, dtype=str).T.fillna("-"))
        s = "name + name * name"
        tokens = Token([(i, i) for i in s.split(" ")])
        status, message = G.isLL1()
        if status:
            dot, processList, syntaxMsg = G.LL1_analyze(tokens)
            dot.render("./output/LL1_analyze.gv", view=True)
            print(*processList, sep="\n")
            print(syntaxMsg)
        else:
            print(message)

    else:
        print("------------LR(1)项集的规范族CC------------")
        CC, CC_dict = G.build_CC()
        print(*G.CCstr(), sep="\n")
        G.CC_DFA().dot("CC_DFA")
        print("------------LR(1) Table------------")
        Action, Goto = G.LR1_table()
        Action_df = pd.DataFrame(Action, index=[EOF] + G.T, columns=range(len(CC))).T.fillna("-")
        Goto_df = pd.DataFrame(Goto, index=G.NT, columns=range(len(CC))).T.fillna("-")
        print(pd.concat([Action_df, Goto_df], keys=["Action", "Goto"], axis=1))
        s = "name + name * name"
        tokens = Token([('name', 'a'), ('+', '+'), ('name', 'b'), ('*', '*'), ('name', 'c')])
        dot, processList, syntaxMsg = G.LR1_analyze(tokens)
        dot.render("./output/LR1_analyze.gv", view=True)
        print(*processList, sep="\n")
        print(syntaxMsg)
