import { digraph } from "graphviz";
import fs from "fs";

const dot = digraph("G");
let idx = 0;
const dfs = (node, id) => {
    if (typeof node === "string") {
        dot.addNode(String(id), { label: 'string', shape: 'doublecircle' });
    } else if (Array.isArray(node)) {
        dot.addNode(String(id), { label: "array", shape: 'circle' });
        node.forEach((value, index) => {
            const son = idx++;
            dot.addEdge(String(id), String(son), { label: String(index) });
            dfs(value, son);
        });
    } else {
        dot.addNode(String(id), { label: "dict", shape: 'circle' });
        for (const [key, value] of Object.entries(node)) {
            const son = idx++;
            dot.addEdge(String(id), String(son), { label: key });
            dfs(value, son);
        }
    }
}
const dfs2 = (node, fa) => {
    if (fa === 0) {
        dot.addNode(String(fa), { label: "root", shape: 'circle' });
    }
    if (typeof node === "string") {
        const cur = idx++;
        dot.addNode(String(cur), { label: node, shape: 'doublecircle' });
        dot.addEdge(String(fa), String(cur));
    } else if (Array.isArray(node)) {
        for (let value of node) {
            dfs2(value, fa);
        }
    } else {
        for (const [key, value] of Object.entries(node)) {
            const son = idx++;
            dot.addNode(String(son), { label: key, shape: 'circle' });
            dot.addEdge(String(fa), String(son));
            dfs2(value, son);
        }
    }
}
const syntaxTree = { "Goal": [{ "Expr": [{ "Expr'": [{ "Expr'": ["ε"] }, { "Term": [{ "Term'": [{ "Term'": ["ε"] }, { "Factor": ["name"] }, "*"] }, { "Factor": ["name"] }] }, "+"] }, { "Term": [{ "Term'": ["ε"] }, { "Factor": ["name"] }] }] }] };
dfs2(syntaxTree, idx++);

const output = dot.to_dot();
fs.writeFileSync("output.dot", output);