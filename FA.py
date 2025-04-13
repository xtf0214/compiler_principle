import pandas as pd
from graphviz import Digraph

EPS = "eps"
EOF = "eof"


class NFA:
    def __init__(self, S: list, sigma: list, delta: list[(str, str, str)], s0: str, A: list):
        self.S = S
        self.sigma = sigma
        self.delta = delta
        self.s0 = s0
        self.A = A
        self.G = {i: {} for i in S}
        for u, w, v in delta:
            self.G[u].setdefault(w, []).append(v)

    @classmethod
    def load_fa(cls, filename: str):
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

    def plot(self, filename: str):
        dot = Digraph(filename)
        for u in self.S:
            dot.node(u, u)
        for u in self.A:
            dot.node(u, u, shape="doublecircle")
        for u, w, v in self.delta:
            dot.edge(u, v, label=w)
        dot.render(f"./output/{filename}.gv")

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

        df = pd.DataFrame(columns=["集合名称", "DFA状态", "NFA状态子集"] + self.sigma)
        T = {}
        q0 = eps_closure([self.s0])
        Q = [q0]
        worklist = [q0]
        while worklist:
            q = worklist.pop(0)
            df.loc[len(df)] = [f"q{len(df)}", f"d{len(df)}", q] + [EPS for c in self.sigma]
            T[Q.index(q)] = {}
            for c in self.sigma:
                t = eps_closure(get_delta(q, c))
                df.at[len(df) - 1, c] = t if t not in Q else f"q{Q.index(t)}"
                if t not in Q:
                    Q.append(t)
                    worklist.append(t)
                T[Q.index(q)][c] = Q.index(t)
        print(df)
        delta = [(str(u), str(w), str(v)) for u, items in T.items() for w, v in items.items()]
        nfa = DFA(
            S=[str(i) for i in T.keys()],
            sigma=self.sigma,
            delta=delta,
            s0="0",
            A=[str(i) for i in range(len(Q)) if set(self.A) & set(Q[i])],
        )
        return nfa


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
                    groupby.setdefault(s_index[v], []).append(k)
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
        s_index = {}
        while T != P:
            s_index = {x: str(i) for i, s in enumerate(T) for x in s}
            P = T
            T = set()
            for p in P:
                T = T | split(p)
        T = list(map(list, T))
        print(T)
        min_dfa = DFA(
            S=[str(i) for i in range(len(T))],
            sigma=self.sigma,
            delta=list({(s_index[u], c, s_index[v]) for u, c, v in self.delta}),
            s0=s_index[self.s0],
            A={s_index[i] for i in self.S if i in self.A},
        )
        return min_dfa

    # def hopcroft(self):
    #     partition = [set(self.S_A), set(self.S) - set(self.S_A)]
    #     worklist = [set(self.S_A), set(self.S) - set(self.S_A)]
    #     while worklist:
    #         s = worklist.pop()
    #         for c in self.sigma:
    #             image = {u for u, w, v in self.delta if w == c and v in s}
    #             for q in partition:
    #                 q1 = q & image
    #                 q2 = q - q1
    #                 if q1 and q2:
    #                     partition.remove(q)
    #                     partition.append(q1)
    #                     partition.append(q2)
    #                     if q in worklist:
    #                         worklist.remove(q)
    #                         worklist.append(q1)
    #                         worklist.append(q2)
    #                     else:
    #                         if len(q1) <= len(q2):
    #                             worklist.append(q1)
    #                         else:
    #                             worklist.append(q2)
    #                     if s == q:
    #                         break
    #     print(partition)
    #     print(sorted(partition))


if __name__ == "__main__":
    nfa = NFA.load_fa("FA1.txt")
    nfa.plot("nfa")
    dfa = nfa.subset_construction()
    dfa.plot("dfa")
    min_dfa = dfa.hopcroft()
    min_dfa.plot("min_dfa")
