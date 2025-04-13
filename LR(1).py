import pandas as pd
from FA import DFA
from Lexer import Lexer, Token

EPS = "eps"
EOF = "$"


class Grammar:
    def __init__(self, T: list[str], NT: list[str], S: str, P: list[tuple[str, str]]):
        self.T = T
        self.NT = NT
        self.S = S
        self.P: dict[str, list[list[str]]] = {}
        for k, v in P:
            self.P.setdefault(k, []).append(v.split(" "))
        self.first = self.first_set()

    def __str__(self):
        return f"(T={self.T}\nNT={self.NT}\nS={self.S}\nP={self.P})"
    @classmethod
    def load_grammer(cls, filename: str):
        with open(filename, "r") as f:
            T, NT, S, P = f.read().replace("eps", EPS).split("\n\n")
            NT = NT.split(" ")
            T = T.split(" ")
            P = [tuple(line.split(" -> ")) for line in P.split("\n")]
            return cls(T, NT, S, P)

    def first_set(self):
        first = {}
        for r in self.T + [EOF, EPS]:
            first[r] = {r}
        for r in self.NT:
            first[r] = set()
        fixed_point = True
        while fixed_point:
            is_changed = False
            for A, rules in self.P.items():
                for rule in rules:
                    rhs = set()
                    for i in range(len(rule)):
                        rhs |= first[rule[i]] - {EPS}
                        if EPS not in first[rule[i]]:
                            break
                    else:
                        if EPS in first[rule[-1]]:
                            rhs.add(EPS)
                    if not rhs <= first[A]:
                        first[A] |= rhs
                        is_changed = True
            fixed_point = is_changed
        return first

    def get_first(self, rule):
        rhs = set()
        for i in range(len(rule)):
            rhs |= self.first[rule[i]] - {EPS}
            if EPS not in self.first[rule[i]]:
                break
        else:
            if EPS in self.first[rule[-1]]:
                rhs.add(EPS)
        return rhs

    def closure(self, s: list) -> list:
        worklist = s.copy()
        while worklist:
            A, beta, delta, a = worklist.pop(0)
            if delta == []:
                continue
            C, delta = delta[0], delta[1:]
            if C in self.NT:
                for gamma in self.P[C]:
                    for b in self.get_first(delta + [a]):
                        if (C, [], gamma, b) not in s:
                            worklist.append((C, [], gamma, b))
                            s.append((C, [], gamma, b))
        return s

    def goto(self, s: list, x: str) -> list:
        worklist = []
        for A, beta, delta, a in s:
            if delta and delta[0] == x:
                worklist.append((A, beta + [delta[0]], delta[1:], a))
        return self.closure(worklist)

    def find_next(self, s: list) -> list:
        move = []
        for A, beta, delta, a in s:
            if delta and delta[0] not in move:
                move.append(delta[0])
        return move

    def get_CC(self, display=True) -> list[list]:
        CC = [self.closure([(self.S, [], self.P[self.S][0], EOF)])]
        CC_dict = {}
        worklist = CC.copy()
        while worklist:
            s = worklist.pop(0)
            CC_dict[CC.index(s)] = {}
            for x in self.find_next(s):
                if (s1 := self.goto(s, x)) not in CC:
                    worklist.append(s1)
                    CC.append(s1)
                CC_dict[CC.index(s)][x] = CC.index(s1)
        if display:
            vis = {0}
            CCi = lambda CCi: ";".join(
                f"[{A} -> {' '.join(beta)} * {' '.join(delta)}, {a}]" for A, beta, delta, a in CCi
            )
            print(f"CC0={{{CCi(CC[0])}}}")
            q = [(-1, 0, 0)]
            while q:
                u, w, v = q.pop(0)
                if u != -1:
                    print(f"CC{v}=goto(CC{u},{w})={{{CCi(CC[v])}}}")
                u = v
                for w, v in CC_dict[u].items():
                    if v in vis:
                        continue
                    vis.add(v)
                    q.append((u, w, v))
        return CC, CC_dict

    def CC_DFA(self):
        CC, CC_dict = self.get_CC(display=False)
        cc_dfa = DFA(
            S=list(map(str, range(len(CC)))),
            sigma=self.T + self.NT + [EOF],
            delta=[(str(u), str(w), str(v)) for u, item in CC_dict.items() for w, v in item.items()],
            s0=str(0),
            A=[str(i) for i in range(len(CC)) if any(not delta for A, beta, delta, a in CC[i])],
        )
        return cc_dfa

    def LR1_table(self, display=True):
        rule_list = [(A, rule) for A, rules in self.P.items() for rule in rules]
        if display:
            print(pd.Series([p[0] + " -> " + " ".join(p[1]) for p in rule_list]))
        CC, CC_dict = self.get_CC(display=False)
        Action = pd.DataFrame(columns=[EOF] + self.T, index=range(len(CC)))
        Goto = pd.DataFrame(columns=self.NT, index=range(len(CC)))
        for u, item in CC_dict.items():
            for w, v in item.items():
                if w in self.T:
                    Action.at[u, w] = f"s{v}"
                else:
                    Goto.at[u, w] = str(v)
        for i in range(len(CC)):
            for A, beta, delta, a in CC[i]:
                if not delta:
                    if (A, beta) == (self.S, self.P[self.S][0]):
                        Action.at[i, a] = "acc"
                    else:
                        Action.at[i, a] = f"r{rule_list.index((A, beta))}"
        if display:
            print(pd.concat([Action, Goto], axis=1).fillna("-"))
        Action.fillna("-", inplace=True)
        Goto.fillna("-", inplace=True)
        return Action, Goto

    def analyze(self, token: Token):
        Action, Goto = self.LR1_table(display=False)
        rule_list = [(A, rule) for A, rules in self.P.items() for rule in rules]
        cur = 0
        stack = ["$"]
        queue = []
        stack.append((self.S, 0))
        type, word = token.next_word()
        queue.append(word)
        error = False
        while True:
            # print(stack)
            w, state = stack[-1]
            if Action.at[state, type].startswith("r"):
                A, rule = rule_list[int(Action.at[state, type][1:])]
                for i in range(len(rule)):
                    stack.pop()
                state = stack[-1][1]
                stack.append((A, int(Goto.at[state, A])))
            elif Action.at[state, type].startswith("s"):
                stack.append((type, int(Action.at[state, type][1:])))
                type, word = token.next_word()
                queue.append(word)
            elif Action.at[state, type] == "acc":
                break
            else:
                exception_word = [k for k, v in Action.loc[state, :].to_dict().items() if v != "-"]
                print(
                    f"error: {''.join(queue[:-1]) + f"\033[0;31m{queue[-1]}\033[0m"} execption work {exception_word} but {type}"
                )
                error = True
                break
        if not error:
            print("success")


if __name__ == "__main__":
    G = Grammar.load_grammer(r"D:\Code\Python\algorithm\Compiler\Expr.txt")
    print(G)
    print("------------LR(1)项集的规范族CC------------")
    G.get_CC()
    G.CC_DFA().plot("CC_DFA")
    print("------------LL(1) Table------------")
    G.LR1_table()
    # G.analyze("()(")
    while True:
        s = input("请输入要分析的字符串：")
        G.analyze(Lexer(s).get_token())
