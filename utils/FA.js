import fs, { symlink } from "fs";
import { digraph } from "graphviz";
import path from "path";

const EPS = "ε";
const EOF = "$";

/**
 * 获取A中是否有x的索引
 * @param {Array<Array>} A
 * @param {Array} x
 * @returns
 */
const indexOf = (A, x) => {
    return A.findIndex((a) => JSON.stringify([...a]) === JSON.stringify([...x]));
};

class FA {
    /**
     * @param {Array<string>} S
     * @param {Array<Array<string>>} sigma
     * @param {Array} delta
     * @param {string} s0
     * @param {Array<string>} A
     */
    constructor(S, sigma, delta, s0, A) {
        this.S = S;
        this.sigma = sigma;
        this.delta = delta;
        this.s0 = s0;
        this.A = A;

        // 构建状态转移图 G
        this.G = {};
        for (let state of S) {
            this.G[state] = {};
        }
        for (let [u, w, v] of delta) {
            if (!this.G[u][w]) this.G[u][w] = [];
            this.G[u][w].push(v);
        }
    }

    /**
     * 加载FA
     * @param {string} filename 文件名
     * @param {FA|NFA|DFA} cls
     * @returns {FA} FA实例
     */
    static load(filename, cls = FA) {
        let content = fs.readFileSync(filename, "utf8").replace(/eps/g, EPS);
        const lines = content
            .trim()
            .split("\n")
            .map((line) => line.trim())
            .filter((line) => line);
        const S = lines[0].split(" ");
        const sigma = lines[1].split(" ");
        const delta = lines.slice(2, -2).map((item) => item.split(" "));
        const s0 = lines[lines.length - 2];
        const A = lines[lines.length - 1].split(" ");
        return new cls(S, sigma, delta, s0, A);
    }

    move(s, w) {
        return this.G[s]?.[w] || [];
    }

    /**
     *
     * @param {string} filename - 文件名
     * @returns {string} - dot源码
     */
    dot(filename = "fa") {
        let dot = `digraph ${filename} {\n`;
        dot += "    rankdir=LR;\n";
        this.S.forEach((state) => {
            state = state.replace('"', '\\"');
            const isStart = state === this.s0;
            const isAccept = this.A.includes(state);
            let style = [];
            style.push(isAccept ? "shape=doublecircle" : "shape=circle");
            dot += `    ${state} [${style.join(",")}];\n`;
        });
        // 添加转移
        let delta = {};
        this.delta.forEach(([from, symbol, to]) => {
            from = from.replace('"', '\\"');
            to = to.replace('"', '\\"');
            symbol = symbol.replace('"', '\\"');
            delta[from] ??= {};
            delta[from][to] ??= [];
            delta[from][to].push(symbol);
        });
        dot += Object.entries(delta).flatMap(([from, item]) =>
            Object.entries(item).map(([to, symlbols]) => `    ${from} -> ${to} [label="${symlbols.join(',')}"];`)
        ).join('\n');

        dot += "}";
        return dot;
        // const dot = new digraph(filename);
        // for (let u of this.S) {
        //     dot.addNode(u).set("label", u);
        //     dot.getNode(u).set("shape", "circle");
        // }
        // for (let a of this.A)
        //     dot.getNode(a).set("shape", "doublecircle");
        // for (let [u, w, v] of this.delta)
        //     dot.addEdge(u, v).set("label", w);
        // fs.writeFileSync(`./output/${filename}.dot`, dot.to_dot());
        // return dot.to_dot();
    }
}

class NFA extends FA {
    /**
     * 加载NFA
     * @param {string} filename 文件名
     * @returns {NFA} NFA实例
     */
    static load(filename) {
        return super.load(filename, NFA);
    }

    /**
     * 子集构造法
     * @returns {[DFA, Array<Array<string>>, Object]} - [DFA, DFA状态子集列表, DFA状态转移表]
     */
    subsetConstruction() {
        /**
         * 获取经c状态转移
         * @param {Array<string>} q
         * @param {string} c
         * @returns {Set<string>}
         */
        const getDelta = (q, c) => {
            let S = new Set();
            for (let state of q) {
                for (let [u, w, v] of this.delta) {
                    if (u === state && w === c) {
                        S.add(v);
                    }
                }
            }
            return S;
        };

        /**
         * 求eps闭包
         * @param {Set<string>} S
         * @returns {Array<string>}
         */
        const eps_closure = (S) => {
            let worklist = [...S];
            let closureSet = [...S];

            while (worklist.length > 0) {
                let x = worklist.shift();
                for (let [u, w, v] of this.delta) {
                    if (u === x && w === EPS && !closureSet.includes(v)) {
                        closureSet.push(v);
                        worklist.push(v);
                    }
                }
            }
            return closureSet.sort();
        };

        let Q = [eps_closure([this.s0])];
        let worklist = [Q[0]];
        let T = {};
        let TT = {};

        while (worklist.length > 0) {
            const q = worklist.shift();
            T[indexOf(Q, q)] = {};
            TT[indexOf(Q, q)] = {};
            for (const c of this.sigma) {
                const t = eps_closure(getDelta(q, c));
                if (t.length === 0) continue;
                T[indexOf(Q, q)][c] = indexOf(Q, t) === -1 ? t : indexOf(Q, t);
                if (indexOf(Q, t) === -1) {
                    Q.push(t);
                    worklist.push(t);
                }
                TT[indexOf(Q, q)][c] = indexOf(Q, t)
            }
        }

        let delta = Object.entries(TT).flatMap(([s, items]) =>
            Object.entries(items).map(([c, t]) => [s, c, String(t)])
        );

        const A = Q.map((_, i) => i)
            .filter((i) => Q[i].some((state) => this.A.includes(state)))
            .map((i) => String(i));

        return [
            new DFA(
                Q.map((_, i) => String(i)),
                this.sigma,
                delta,
                String(0),
                A
            ),
            Q,
            T,
        ];
    }
}

class DFA extends NFA {
    /**
     * 加载DFA
     * @param {string} filename 文件名
     * @returns {DFA} DFA实例
     */
    static load(filename) {
        return super.load(filename, DFA);
    }
    move(s, w) {
        return this.G[s]?.[w]?.[0] || null;
    }

    /**
     * hopcroft算法
     * @returns {[DFA, Array<Array<string>>]} - [最小化DFA, DFA构建过程]
     */
    hopcroft() {
        let partition = [
            new Set(this.A),
            new Set(this.S.filter((s) => !this.A.includes(s))),
        ];
        let worklist = [new Set(this.A)];
        let PI = [];
        while (worklist.length > 0) {
            let s = worklist.pop();
            for (let c of this.sigma) {
                let image = new Set();
                for (let [u, w, v] of this.delta) {
                    if (w === c && s.has(v)) {
                        image.add(u);
                    }
                }
                for (let q of partition) {
                    let q1 = new Set([...q].filter((x) => image.has(x)));
                    let q2 = new Set([...q].filter((x) => !image.has(x)));

                    if (q1.size > 0 && q2.size > 0) {
                        PI.push([
                            partition.map((item) => Array.from(item)),
                            Array.from(q),
                            c,
                            Array.from(q1),
                            Array.from(q2),
                        ]);
                        partition.splice(indexOf(partition, q), 1, q1, q2);
                        if (indexOf(worklist, q) != -1) {
                            worklist.splice(indexOf(worklist, q), 1, q1, q2);
                        } else {
                            worklist.push(q1.size <= q2.size ? q1 : q2);
                        }
                    }
                }
            }
        }
        PI.push([partition.map((item) => Array.from(item)), [], null, [], []]);
        let stateMap = {};
        partition.forEach((group, i) => {
            const x = Math.min(...Array.from(group).map((item) => Number(item)));
            for (let s of group) {
                stateMap[s] = String(x);
            }
        });
        let S = Object.values(stateMap);
        // let S = partition.map((_, i) => String(i));
        let delta = [];
        for (let [u, w, v] of this.delta) {
            if (indexOf(delta, [stateMap[u], w, stateMap[v]]) === -1) {
                delta.push([stateMap[u], w, stateMap[v]]);
            }
        }
        let A = [...new Set(this.A.map((s) => stateMap[s]))];
        return [new DFA(S, this.sigma, delta, stateMap[this.s0], A), PI];
    }
}
export { FA, NFA, DFA };

// const nfa = NFA.load(path.join('input', 'FA', 'test1_FA.txt'));
// console.log("NFA:")
// console.table(nfa.G);
// nfa.dot("nfa");

// const [dfa, Q, T] = nfa.subsetConstruction();
// console.log("subsetConstruction:");
// console.table(T);
// console.log("DFA:")
// console.table(dfa.G); // 输出DFA的状态、字母表、转移函数、初始状态和接受状态
// dfa.dot("dfa");

// const [minDfa, PI] = dfa.hopcroft();
// console.log("hopcroft:")
// console.table(PI);
// console.log("minDfa:")
// console.table(minDfa.G); // 输出最小化DFA的状态、字母表、转移函数、初始状态和接受状态
// minDfa.dot("min_dfa");
