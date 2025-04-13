import random
import pandas as pd
import math

EPS = "eps"
EOF = "eof"


class Grammar:
    def __init__(self, T: list[str], NT: list[str], S: str, P: list[tuple[str, str]]):
        self.T = T
        self.NT = NT
        self.S = S
        self.P: dict[str, list[list[str]]] = {}
        for k, v in P:
            self.P.setdefault(k, []).append(v.split(" "))

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

    def follow_set(self):
        first = self.first_set()
        follow: dict[str, set] = {}
        for r in self.NT:
            follow[r] = set()
        follow[self.S] = {EOF}
        fixed_point = True
        while fixed_point:
            is_changed = False
            for A, rules in self.P.items():
                for rule in rules:
                    trailer = follow[A].copy()
                    for i in range(len(rule) - 1, -1, -1):
                        if rule[i] in self.NT:
                            if not trailer <= follow[rule[i]]:
                                is_changed = True
                                follow[rule[i]] |= trailer
                            if EPS in first[rule[i]]:
                                trailer |= first[A] - {EPS}
                            else:
                                trailer = first[rule[i]]
                        else:
                            trailer = first[rule[i]].copy()
            fixed_point = is_changed
        return follow

    def select_set(self):

        first = self.first_set()
        follow = self.follow_set()
        select = {}

        def get_first(rule):
            rhs = set()
            for i in range(len(rule)):
                rhs |= first[rule[i]] - {EPS}
                if EPS not in first[rule[i]]:
                    break
            else:
                if EPS in first[rule[-1]]:
                    rhs.add(EPS)
            return rhs

        for A, rules in self.P.items():
            for rule in rules:
                first_rule = get_first(rule)
                if EPS not in first_rule:
                    select[(A, " ".join(rule))] = first_rule
                else:
                    select[(A, " ".join(rule))] = first_rule | follow[A]
        return select

    def LL1_table(self):
        select = self.select_set()
        df = pd.DataFrame(index=self.NT, columns=[EOF] + self.T)
        rule_list = []
        for A, rules in self.P.items():
            for rule in rules:
                p = (A, " ".join(rule))
                rule_list.append(p[0] + " -> " + p[1])
                for w in select[p] - {EPS}:
                    df.at[A, w] = len(rule_list) - 1
                if EPS in select[p]:
                    df.at[A, EOF] = len(rule_list) - 1
        print(pd.Series(rule_list))
        print(df)

    def derivation(self, s: list[str]):
        print("".join(s))
        for i in range(len(s)):
            if s[i] in self.NT:
                self.derivation(s[:i] + random.choice(self.P[s[i]]) + s[i + 1 :])


if __name__ == "__main__":
    G = Grammar.load_grammer("Expr2.txt")
    print("------------First------------")
    print(pd.Series(G.first_set()))
    print("------------Follow------------")
    print(pd.Series(G.follow_set()))
    print("------------Select------------")
    print(pd.Series(G.select_set()))
    print("------------LL(1) Table------------")
    G.LL1_table()
