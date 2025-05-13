import pandas as pd
from graphviz import Digraph

EPS = "ε"
EOF = "$"


class FA:
    def __init__(self, S: list, sigma: list, delta: list, s0, A: list):
        self.S = S
        self.sigma = sigma
        self.delta = delta
        self.s0 = s0
        self.A = A
        self.G = {i: {} for i in S}
        for u, w, v in delta:
            self.G[u].setdefault(w, []).append(v)

    @classmethod
    def load(cls, filename: str):
        with open(filename, "r") as f:
            S, sigma, delta, s0, A = f.read().replace("eps", EPS).split("\n\n")
            S = S.split(" ")
            sigma = sigma.split(" ")
            delta = [tuple(item.split(" ")) for item in delta.split("\n")]
            A = A.split(" ")
            return cls(S, sigma, delta, s0, A)

    def __str__(self):
        return f"(S={self.S}\nsigma={self.sigma}\ndelta={self.delta}\ns0={self.s0}\nA={self.A})"

    def move(self, s: str, w: str):
        return self.G[s][w] if w in self.G[s] else []

    def dot(self, filename: str, view: bool = False):
        dot = Digraph(filename)
        for u in self.S:
            dot.node(u, u, shape="circle")
        for u in self.A:
            dot.node(u, u, shape="doublecircle")
        for u, w, v in self.delta:
            dot.edge(u, v, label=w)
        dot.render(f"./output/{filename}.gv", view=view)


class NFA(FA):

    def dfs_eps_closure(self):
        """离线计算 eps_closure"""
        E = {s: {} for s in self.S}

        def dfs(x):
            if E[x]:
                return
            E[x] = {x}
            for u, w, v in self.delta:
                if x == u and v != u and w == EPS:
                    dfs(v)
                    E[u] = E[u] | E[v]

        for s in self.S:
            dfs(s)
        print(E)

    def eps_closure(self):
        """离线计算 eps_closure"""
        E = {s: {s} for s in self.S}
        worklist = self.S.copy()
        iter_cnt = 0
        while worklist:
            x = worklist.pop(0)
            t = {x}
            for u, w, v in self.delta:
                if u == x and w == EPS:
                    t = t | E[v]
            if t != E[x]:
                E[x] = t
                for u, w, v in self.delta:
                    if v == x and w == EPS and u not in worklist:
                        worklist.append(u)
            iter_cnt += 1
        print(E, iter_cnt)

    def subset_construction(self):
        """子集构造法"""

        def get_delta(q: list, c: str) -> list:
            S = []
            for x in q:
                for u, w, v in self.delta:
                    if u == x and w == c and v not in S:
                        S.append(v)
            return S

        def eps_closure(S: list) -> list:
            # 不动点计算
            worklist = S.copy()
            S = S.copy()
            while worklist:
                x = worklist.pop(0)
                for u, w, v in self.delta:
                    if u == x and w == EPS and v not in S:
                        S.append(v)
                        worklist.append(v)
            return sorted(S)

        Q = [eps_closure([self.s0])]
        worklist = [Q[0]]
        T = {}
        TT = {}

        while worklist:
            q = worklist.pop(0)
            T[Q.index(q)] = {}
            TT[Q.index(q)] = {}
            for c in self.sigma:
                t = eps_closure(get_delta(q, c))
                T[Q.index(q)][c] = t if t not in Q else f"{Q.index(t)}"
                if t not in Q:
                    Q.append(t)
                    worklist.append(t)
                TT[Q.index(q)][c] = Q.index(t)
        delta = [(str(u), str(w), str(v)) for u, items in TT.items() for w, v in items.items()]
        dfa = DFA(
            S=[str(i) for i in T.keys()],
            sigma=self.sigma,
            delta=delta,
            s0=str(0),
            A=[str(i) for i in range(len(Q)) if set(self.A) & set(Q[i])],
        )
        return dfa, Q, T


class DFA(NFA):

    def move(self, s: str, w: str):
        return self.G[s][w][0] if w in self.G[s] else None

    def hopcroft(self):
        def split_into(s, c):
            """将状态集s按照c分割成s1和s2"""
            dst = {}
            s1, s2 = set(), set()
            for u in s:
                v = self.move(u, c)
                if v:
                    # 经c可转移
                    dst[u] = v
                    s1.add(u)
                else:
                    # 经c不可转移
                    s2.add(u)
            if not s2:
                # 不存在经c不可转移的点,按照转移点所属集合切分
                groupby = {}
                for k, v in dst.items():
                    groupby.setdefault(stateMap[v], []).append(k)
                if len(groupby) > 1:
                    print(s, c, list(groupby.values()))
                s1 = set(next(iter(groupby.values())))
                s2 = s - s1
            return frozenset(s1), frozenset(s2)

        def split(s):
            for c in self.sigma:
                s1, s2 = split_into(s, c)
                if s2:
                    return {s1, s2}
            return {s}

        T = {frozenset(self.A), frozenset(self.S) - frozenset(self.A)}
        P = set()
        stateMap = {}
        while T != P:
            stateMap = {x: str(i) for i, s in enumerate(T) for x in s}
            P = T
            T = set()
            for p in P:
                T = T | split(p)
        T = list(map(list, T))
        print(T)
        min_dfa = DFA(
            S=[str(i) for i in range(len(T))],
            sigma=self.sigma,
            delta=list({(stateMap[u], c, stateMap[v]) for u, c, v in self.delta}),
            s0=stateMap[self.s0],
            A=list({stateMap[i] for i in self.S if i in self.A}),
        )
        return min_dfa

    def hopcroft1(self):
        partition = [set(self.A), set(self.S) - set(self.A)]
        worklist = [set(self.A), set(self.S) - set(self.A)]
        PI = []
        while worklist:
            s = worklist.pop()
            for c in self.sigma:
                image = {u for u, w, v in self.delta if w == c and v in s}
                for q in partition:
                    q1 = q & image
                    q2 = q - q1
                    if q1 and q2:
                        PI.append((partition, q, c, q1, q2))
                        partition.remove(q)
                        partition.append(q1)
                        partition.append(q2)
                        if q in worklist:
                            worklist.remove(q)
                            worklist.append(q1)
                            worklist.append(q2)
                        else:
                            worklist.append(q1 if len(q1) <= len(q2) else q2)
        PI.append((partition, {}, None, {}, {}))
        stateMap = {x: min(s) for s in partition for x in s}
        min_dfa = DFA(
            S=[str(i) for i in stateMap.values()],
            sigma=self.sigma,
            delta=list({(stateMap[u], c, stateMap[v]) for u, c, v in self.delta}),
            s0=str(stateMap[self.s0]),
            A=list({str(stateMap[i]) for i in self.A}),
        )
        return min_dfa, PI


if __name__ == "__main__":
    nfa = NFA.load("./input/FA/test1_FA.txt")
    nfa.dot("nfa", view=True)
    dfa, Q, T = nfa.subset_construction()
    print("----------子集构造法----------")
    df1 = pd.DataFrame(T, index=dfa.sigma).T.rename_axis("集合名称")
    df1.insert(0, "DFA状态子集", Q)
    print(df1)
    dfa.dot("dfa", view=True)
    print("----------Hopcroft算法----------")
    min_dfa, PI = dfa.hopcroft1()
    print(pd.DataFrame(PI))
    min_dfa.dot("min_dfa", view=True)
