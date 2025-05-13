import { DFA } from './FA.js';
import fs from 'fs';
import path from 'path';
import { Token } from './Lexer.js';
import { digraph } from "graphviz";
import { error } from 'console';


const EPS = 'ε';
const EOF = '$';


/**
 * 获取A中是否有x的索引
 * @param {Array<Array>} A
 * @param {Array} x
 * @returns
 */
const indexOf = (A, x) => {
    return A.findIndex((a) => JSON.stringify([...a]) === JSON.stringify([...x]));
};

class Grammar {
    /**
     * @param {string[]} T 终结符集合
     * @param {string[]} NT 非终结符集合
     * @param {string} S 起始符号
     * @param {Array<[string, Array<string>]>} P 产生式规则
     */
    constructor(T, NT, S, P) {

        this.T = T;
        this.NT = NT;
        this.S = S;
        this.P = P;
        this.Pstr = P.map(([A, beta]) => this.getPstr(A, beta));
        this.FirstSet = null;
        this.FollowSet = null;
        this.SelectSet = null;
        this.LL1TABLE = null;
        this.CC = null;
        this.CC_dict = null;
        this.Action = null;
        this.Goto = null;
    }

    /**
     * @param {string} A 产生式左部
     * @param {Array<string>} beta 产生式右部
     * @returns {string} 产生式
     */
    getPstr(A, beta) {
        return A + ' -> ' + beta.join(' ');
    }
    /**
     * @param {string} Pstring 产生式
     * @returns {Array<string, Array<string>>} 产生式左部
     */
    getP(s) {
        return this.P[this.Pstr.indexOf(s)];
    }


    /**
     * @param {string} filename 语法文件路径
     * @returns {Grammar} 解析后的语法对象
     */
    static load(filename) {
        let content = fs.readFileSync(filename, "utf8").replace(/eps/g, EPS);
        const lines = content.trim().split("\n").map((line) => line.trim()).filter((line) => line);
        const T = lines[0].split(" ");
        const NT = lines[1].split(" ");
        const S = lines[2];
        const P = lines.slice(3).map((line) => line.split(" -> ")).map(([k, v]) => [k, v.split(" ")]);
        return new Grammar(T, NT, S, P);
    }

    /**
     * @returns {Object<string, Array<string>>} 各符号的FIRST集合
    */
    firstSet() {
        if (this.FirstSet) return this.FirstSet;
        this.FirstSet = {};
        const first = {};
        for (const r of [...this.T, EOF, EPS]) {
            first[r] = new Set([r]);
        }
        for (const r of this.NT) {
            first[r] = new Set();
        }

        let fixedPoint = true;
        while (fixedPoint) {
            let isChanged = false;
            for (const [A, beta] of this.P) {
                let allHasEPS = true;
                let rhs = new Set();
                for (let i = 0; i < beta.length; i++) {
                    rhs = new Set([...rhs, ...first[beta[i]]]);
                    rhs.delete(EPS);
                    if (!first[beta[i]].has(EPS)) {
                        allHasEPS = false;
                        break;
                    }
                }
                if (allHasEPS) {
                    rhs.add(EPS);
                }
                if (![...rhs].every(x => first[A].has(x))) {
                    rhs.forEach(x => first[A].add(x));
                    isChanged = true;
                }
            }
            fixedPoint = isChanged;
        }
        Object.entries(first).forEach(([k, v]) => {
            this.FirstSet[k] = Array.from(v);
        });
        return this.FirstSet;
    }

    /**
     * @param {Array<string>} beta 产生式右部
     * @returns {Set<string>} 右部的FIRST集合
     */
    getFirst(beta) {
        const first = this.firstSet();
        let rhs = new Set();
        let allHasEPS = true;
        for (let i = 0; i < beta.length; i++) {
            rhs = new Set([...rhs, ...first[beta[i]]]);
            rhs.delete(EPS);
            if (!first[beta[i]].includes(EPS)) {
                allHasEPS = false;
                break;
            }
        }
        if (allHasEPS) {
            rhs.add(EPS);
        }
        return rhs;
    };

    /**
     * @returns {Object<string, Array<string>>} 各符号的FOLLOW集合
     */
    followSet() {
        if (this.FollowSet) return this.FollowSet;
        this.FollowSet = {};
        const first = this.firstSet();
        const follow = {};
        for (const r of this.NT) {
            follow[r] = new Set();
        }
        follow[this.S] = new Set([EOF]);

        let fixedPoint = true;
        while (fixedPoint) {
            let isChanged = false;
            for (const [A, beta] of this.P) {
                let trailer = new Set(follow[A]);
                for (let i = beta.length - 1; i >= 0; i--) {
                    if (this.NT.includes(beta[i])) {
                        if (![...trailer].every(x => follow[beta[i]].has(x))) {
                            isChanged = true;
                            trailer.forEach(x => follow[beta[i]].add(x));
                        }
                        if (first[beta[i]].includes(EPS)) {
                            trailer = new Set([...trailer, ...first[A]]);
                            trailer.delete(EPS);
                        } else {
                            trailer = new Set(first[beta[i]]);
                        }
                    } else {
                        trailer = new Set(first[beta[i]]);
                    }

                }
            }
            fixedPoint = isChanged;
        }
        Object.entries(follow).forEach(([k, v]) => {
            this.FollowSet[k] = Array.from(v);
        });
        return this.FollowSet;
    }

    /**
     * @returns {Object<string, Array<string>>} 选择集合
     */
    selectSet() {
        if (this.SelectSet) return this.SelectSet;
        this.SelectSet = {};
        const first = this.firstSet();
        const follow = this.followSet();
        const select = {};

        for (const [A, beta] of this.P) {
            const firstRule = this.getFirst(beta);
            const p = this.getPstr(A, beta);
            if (!firstRule.has(EPS)) {
                select[p] = firstRule;
            } else {
                select[p] = new Set([...firstRule, ...follow[A]]);
            }
        }
        Object.entries(select).forEach(([k, v]) => {
            this.SelectSet[k] = Array.from(v);
        });
        return this.SelectSet;
    }

    /**
     * 打印选择集合
     * @returns {Array<string>}
     */
    isLL1() {
        const hasLeftRecursion = this.P.some(([A, beta]) => beta[0] === A);
        if (hasLeftRecursion) {
            return "含有直接左递归，不是LL(1)文法";
        }
        /**
         * 求集合的交集
         * @param {Array<Set>} sets
         * @returns {Set}
         */
        const Aset = new Set(this.P.map(([A, beta]) => A));
        const select = this.selectSet();
        const hasBacktrack = Array.from(Aset).some((A) => {
            const sets = Object.entries(select).filter(([Pstr1]) => this.getP(Pstr1)[0] === A).map(([A2, s]) => s);
            const intersection = new Set();
            let isIntersect = false;
            sets.forEach(s => {
                for (const x of s) {
                    if (intersection.has(x)) {
                        isIntersect = true;
                    }
                    else {
                        intersection.add(x);
                    }
                }
            });
            return isIntersect;
        });
        if (hasBacktrack) {
            return "存在回溯，不是LL(1)文法";
        } else {
            return "是LL(1)文法";
        }
    }

    /**
     * 生成并打印LL(1)分析表
     * @returns {Object<string, Object<string, number>>}
     */
    LL1Table() {
        if (this.LL1TABLE) return this.LL1TABLE;
        const select = this.selectSet();
        const table = {};

        let idx = 0;
        for (const [A, beta] of this.P) {
            table[A] ??= {};
            const p = this.getPstr(A, beta);
            for (const w of select[p]) {
                if (w !== EPS) {
                    table[A][w] = idx;
                }
            }
            if (select[p].includes(EPS)) {
                table[A][EOF] = idx;
            }
            idx++;
        }
        this.LL1TABLE = table;
        return this.LL1TABLE;
    }
    /**
     * LL(1)分析
     * @param {Array<Token>} token
     * @returns {Array<string>}
     */
    LL1analyze(token) {
        const table = this.LL1Table();
        const stack = [EOF, this.S];
        const queue = [];
        let [type, word] = token.peekWord();
        let error = false;
        const processList = [];
        let syntaxMsg = '';
        let syntaxTree = { [this.S]: [] };
        let syntaxStack = [syntaxTree];
        queue.push(word);
        processList.push([Array.from(stack), token.getTokens(), '-']);
        while (true) {
            let focus = stack[stack.length - 1];
            let node = syntaxStack[syntaxStack.length - 1];
            if (focus === EOF && type == EOF) break;
            else if (this.T.includes(focus) || focus === EOF) {
                if (focus === type) {
                    stack.pop();
                    syntaxStack.pop();
                    token.nextWord();
                    [type, word] = token.peekWord();
                    queue.push(word);
                    processList.push([Array.from(stack), token.getTokens(), '→']);
                } else {
                    syntaxMsg = `syntax error: ${queue.join(' ')} gived ${type}`;
                    processList.push([Array.from(stack), token.getTokens(), 'error']);
                    node[focus].push(type + 'error');
                    error = true;
                    break;
                }
            } else if (this.NT.includes(focus)) {
                const idx = table[focus][type];
                if (idx !== undefined) {
                    stack.pop();
                    syntaxStack.pop();
                    stack.push(...Array.from(this.P[idx][1]).reverse());
                    processList.push([Array.from(stack).filter(a => a !== EPS), token.getTokens(), String(idx)]);
                    for (let k of Array.from(this.P[idx][1]).reverse()) {
                        let t = (this.T.includes(k) || k == EPS) ? k : { [k]: [] }
                        node[focus].push(t);
                        syntaxStack.push(t);
                    }
                } else {
                    const exceptionWords = Object.entries(table[focus]).map(([key, value]) => key);
                    syntaxMsg = `syntax error: ${queue.join(' ')} excepted ${exceptionWords} but gived ${type}`;
                    processList.push([Array.from(stack), token.getTokens(), 'error']);
                    node[focus].push(type + 'error');
                    error = true;
                    break;
                }
            } else {
                stack.pop();
                syntaxStack.pop();
            }
            console.log(processList[processList.length - 1]);
        }
        const reverse = (node) => {
            if (typeof node === "string") return;
            else if (Array.isArray(node)) { node.reverse(); for (let k of node) reverse(k); }
            else for (const k in node) reverse(node[k]);
        };
        reverse(syntaxTree);
        const dot = this.buildSyntaxTreeDot(syntaxTree);
        if (!error) {
            return [dot.to_dot(), processList, "success"];
        } else {
            return [dot.to_dot(), processList, syntaxMsg];
        }
    }


    /**
     * 求当前LR(1)项集闭包
     * @param {Array<string>} s LR(1)项集
     * @returns {Array<string>} LR(1)项集
     */
    closure(s) {
        const worklist = [...s];
        while (worklist.length > 0) {
            const [A, beta, delta, a] = worklist.shift();
            if (delta.length === 0) continue;
            const [C, ...restDelta] = delta;
            if (this.NT.includes(C)) {
                for (const [_C, gamma] of this.P.filter(([A, beta]) => A === C)) {
                    for (const b of this.getFirst([...restDelta, a])) {
                        const item = [C, [], gamma, b];
                        if (indexOf(s, item) === -1) {
                            worklist.push(item);
                            s.push(item);
                        }
                    }
                }
            }
        }
        return s.sort();
    }

    /**
     * 根据当前的LR(1)项集和符号，转移到下一个LR(1)项集
     * @param {Array<string>} s LR(1)项集
     * @param {string} x 符号
     * @returns {Array<string>} 转移后的LR(1)项集
     */
    goto(s, x) {
        const worklist = [];
        for (const [A, beta, delta, a] of s) {
            if (delta.length > 0 && delta[0] === x) {
                worklist.push([A, [...beta, delta[0]], delta.slice(1), a]);
            }
        }
        return this.closure(worklist);
    }

    /**
     * 根据当前的LR(1)项集，找到可转移的符号
     * @param {Array<string>} s LR(1)项集
     * @returns {Array<string>} 可转移的符号
     */
    findNext(s) {
        const move = [];
        for (const [A, beta, delta, a] of s) {
            if (delta.length > 0 && !move.includes(delta[0])) {
                move.push(delta[0]);
            }
        }
        return [...this.T.filter(x => move.includes(x)), ...this.NT.filter(x => move.includes(x))];
    }

    /**
     * 构建LR(1)项集的规范族CC
     * @returns {Array<Array<Array<string>>>}
     */
    getCC() {
        if (this.CC && this.CC_dict) return [this.CC, this.CC_dict];
        const CC = [this.closure([[this.S, [], this.P[0][1], EOF]])];
        const CC_dict = {};
        const worklist = [...CC];

        while (worklist.length > 0) {
            const s = worklist.shift();
            CC_dict[indexOf(CC, s)] = {};
            for (const x of this.findNext(s)) {
                const s1 = this.goto(s, x);
                if (indexOf(CC, s1) === -1) {
                    worklist.push(s1);
                    CC.push(s1);
                }
                CC_dict[indexOf(CC, s)][x] = indexOf(CC, s1);
            }
        }
        this.CC = CC;
        this.CC_dict = CC_dict;
        return [this.CC, this.CC_dict];
    }
    /**
     * 打印LR(1)项集的规范族CC
     * @returns {Array<string>}
     */
    CCstr() {
        const [CC, CC_dict] = this.getCC();
        let printed = [];
        let CC_str = [];
        const CCi = CCi => CCi.map(([A, beta, delta, a]) => `[${A} -> ${beta.join(' ')} * ${delta.join(' ')}, ${a}]`).join(';');
        CC_str.push(`CC0={${CCi(CC[0])}}`);
        Object.entries(CC_dict).forEach(([u, item]) =>
            Object.entries(item).forEach(([w, v]) => {
                if (!printed.includes(v)) {
                    printed.push(v);
                    CC_str.push(`CC${v}=goto(CC${u},${w})={${CCi(CC[v])}}`)
                }
            })
        );
        return CC_str;
    }


    /**
     * 构建LR(1)项集的规范族CC对应的句柄查找DFA
     * @returns {DFA}
     */
    CC_DFA() {
        const [CC, CC_dict] = this.getCC(false);
        return new DFA(
            Object.keys(CC_dict),
            [...this.T, ...this.NT, EOF],
            Object.entries(CC_dict).flatMap(([u, item]) =>
                Object.entries(item).map(([w, v]) => [String(u), String(w), String(v)])
            ),
            '0',
            CC.map((cc, i) => i.toString()).filter((_, i) =>
                CC[i].some(([A, beta, delta, a]) => delta.length === 0)
            )
        );
    }

    /**
     * 构建LR(1)项集的规范族CC对应的LR(1)分析表
     * @returns {Object<string, Object<string, string>>}
     */
    LR1Table() {
        if (this.Action && this.Goto) return [this.Action, this.Goto];
        const [CC, CC_dict] = this.getCC();
        const Action = {};
        const Goto = {};
        for (const [u, item] of Object.entries(CC_dict)) {
            Action[u] = {};
            Goto[u] = {};
            for (const [w, v] of Object.entries(item)) {
                if (this.T.includes(w)) {
                    Action[u][w] = `s${v}`;
                } else {
                    Goto[u][w] = `${v}`;
                }
            }
        }
        for (let i = 0; i < CC.length; i++) {
            for (const [A, beta, delta, a] of CC[i]) {
                if (delta.length === 0) {
                    if (A === this.S && JSON.stringify(beta) === JSON.stringify(this.P[0][1])) {
                        Action[i][a] = 'acc';
                    } else {
                        Action[i][a] = `r${this.Pstr.indexOf(this.getPstr(A, beta))}`;
                    }
                }
            }
        }
        this.Action = Action;
        this.Goto = Goto;
        return [Action, Goto];
    }

    /**
     * 对输入串进行LR(1)分析
     * @param {Token} token 输入串
     * @returns {Array<string>} 分析过程
     */
    LR1analyze(token) {
        const [Action, Goto] = this.LR1Table(false);
        const stack = [];
        const queue = [];
        let [type, word] = token.nextWord();
        stack.push([EOF, '0']);
        queue.push(word);
        let error = false;
        const processList = [];
        let syntaxMsg = "";
        let syntaxTree = [];
        while (true) {
            const [w, state] = stack[stack.length - 1];
            const action = Action[state][type];
            if (action === undefined) {
                processList.push([state, type, Array.from(stack), [], 'error']);
                const exceptionWords = Object.entries(Action[state]).map(([key, value]) => key);
                syntaxMsg = `syntax error: ${queue.join(' ')} excepted ${exceptionWords} but gived ${type}`;
                error = true;
                break;
            }
            if (action.startsWith("r")) {
                const [A, beta] = this.P[action.slice(1)];
                processList.push([state, type, Array.from(stack), beta, action]);
                let subTree = [];
                for (let i = 0; i < beta.length; i++) {
                    stack.pop();
                    subTree.unshift(syntaxTree.pop());
                }
                syntaxTree.push({ [A]: subTree });
                const [_, newState] = stack[stack.length - 1];
                stack.push([A, (Goto[newState][A])]);
            } else if (action.startsWith("s")) {
                processList.push([state, type, Array.from(stack), [], action]);
                stack.push([type, action.slice(1)]);
                syntaxTree.push(type);
                [type, word] = token.nextWord();
                queue.push(word);
            } else if (action === "acc") {
                syntaxTree = [{ [this.S]: syntaxTree }];
                processList.push([state, type, Array.from(stack), this.P[0][1], action]);
                break;
            }
        }
        const dot = this.buildSyntaxTreeDot(syntaxTree);
        if (!error) {
            return [dot.to_dot(), processList, "success"];
        } else {
            return [dot.to_dot(), processList, syntaxMsg];
        }
    }


    /**
     * 根据对象生成DOT语法树
     * @param {Object} processList 分析过程
     * @returns {digraph} 语法树
    */
    buildSyntaxTreeDot(syntaxTree) {
        const dot = new digraph("fa");
        let idx = 0;
        const dfs = (node, fa) => {
            if (typeof node === "string") {
                const cur = idx++;
                dot.addNode(String(cur), { label: node, shape: 'doublecircle' });
                if (fa !== 0) {
                    dot.addEdge(String(fa), String(cur));
                }
            } else if (Array.isArray(node)) {
                for (let value of node) {
                    dfs(value, fa);
                }
            } else {
                for (const [key, value] of Object.entries(node)) {
                    const son = idx++;
                    dot.addNode(String(son), { label: key, shape: 'circle' });
                    if (fa !== 0) {
                        dot.addEdge(String(fa), String(son));
                    }
                    dfs(value, son);
                }
            }
        }
        dfs(syntaxTree, idx++);
        return dot;
    }
}

export { Grammar };

// const filename = path.join('input', 'Grammar', 'Expr_G.txt');
// const grammar = Grammar.load(filename);
// if (filename.includes("LL1")) {
//     console.log("------------First------------")
//     console.table(grammar.firstSet());
//     console.log("------------Follow------------")
//     console.table(grammar.followSet());
//     console.log("------------Select------------")
//     console.table(grammar.selectSet());
//     console.log("------------LL(1) Table------------")
//     console.table(grammar.Pstr);
//     console.table(grammar.LL1Table());
//     const s = "name + name * name";
//     const tokens = new Token(s.split(" ").map(i => [i, i]));
//     const [dot, processList, syntaxMsg] = grammar.LL1analyze(tokens);
//     console.table(processList);
//     console.log(syntaxMsg);
//     fs.writeFileSync(path.join('output', 'LL1_analyze.dot'), dot);
// } else {
//     console.log("------------LR(1)项集的规范族CC------------")
//     console.log(grammar.CCstr());
//     fs.writeFileSync(path.join('output', 'CC_DFA.dot'), grammar.CC_DFA().dot("CC_DFA"));
//     const [Action, Goto] = grammar.LR1Table();
//     console.log("------------Action Table------------")
//     console.table(Action);
//     console.log("------------Goto Table------------")
//     console.table(Goto);
//     const s = "name + name * name";
//     const tokens = new Token(s.split(" ").map(i => [i, i]));
//     const [dot, processList, syntaxMsg] = grammar.LR1analyze(tokens);
//     console.table(processList);
//     console.log(syntaxMsg);
//     fs.writeFileSync(path.join('output', 'LR1_analyze.dot'), dot);
// }