import { DFA } from "./FA.js";
import fs from "fs";

const EOF = "$";

class Token {
    constructor(tokens) {
        this.tokens = tokens;
        this.pos = 0;
    }

    /**
     * @returns {[string, string]}
     */
    nextWord() {
        if (this.pos >= this.tokens.length) {
            return [EOF, EOF];
        }
        const word = this.tokens[this.pos];
        this.pos += 1;
        return word;
    }
    /**
     * @returns {[string, string]}
     */
    peekWord() {
        if (this.pos >= this.tokens.length) {
            return [EOF, EOF];
        }
        return this.tokens[this.pos];
    }
    /**
     * @returns {Array<[string, string]>}
     */
    getTokens() {
        return [...this.tokens.slice(0, this.pos).map(([x]) => x), '↑', ...this.tokens.slice(this.pos).map(([x]) => x)];
    }
}

class CharStream {
    constructor(inputString) {
        this.input = inputString + EOF;
        this.pos = 0;
    }

    /**
     * @returns {boolean}
     */
    hasNext() {
        return this.pos < this.input.length - 1;
    }

    /**
     * @returns {string}
     */
    nextChar() {
        if (this.pos < this.input.length) {
            const char = this.input[this.pos];
            this.pos += 1;
            return char;
        } else {
            this.pos += 1;
            return EOF;
        }
    }

    rollBack() {
        if (this.pos > 0) {
            this.pos -= 1;
        }
    }
}

class Lexer {

    /**
     * @param {DFA} DFA实例
     * @param {Object} config 配置文件对象
     * @returns {Lexer} 词法分析器
     */
    constructor(dfa, config) {
        this.S = dfa.S;
        this.s0 = dfa.s0;
        this.delta = {};
        for (let [s, c, t] of dfa.delta) {
            if (!this.delta[s]) this.delta[s] = {};
            this.delta[s][c] = t;
        }
        this.A = dfa.A;
        this.Type = config.Type;
        this.charCat = config.charCat;
        this.keyword = config.keyword;
        this.charStream = null;
    }

    /**
     * 词法分析
     * @param {string} inputString 输入字符串
     * @returns {Lexer} 词法分析器
     */
    analyze(inputString) {
        this.charStream = new CharStream(inputString);
        return this;
    }

    /**
     * @returns {[string, string]} 下一个词
     */
    nextWord() {
        if (!this.charStream.hasNext()) {
            return [EOF, EOF];
        }

        let state = this.s0;
        let lexem = "";
        const stack = ["bad"];

        while (state !== "err") {
            const char = this.charStream.nextChar();
            lexem += char;
            if (this.A.includes(state)) {
                stack.length = 0; // clear stack
            }

            stack.push(state);

            const item = Object.entries(this.charCat).find(([key, value]) =>
                value.includes(char)
            );
            const cat = item ? item[0] : "other";
            if (this.delta[state] && this.delta[state][cat]) {
                state = this.delta[state][cat];
            } else {
                state = "err";
            }
        }

        while (!this.A.includes(state) && state !== "bad") {
            state = stack.pop();
            lexem = lexem.slice(0, -1);
            this.charStream.rollBack();
        }

        if (this.A.includes(state)) {
            if (this.keyword.includes(lexem)) {
                return [lexem, lexem]
            } else if (this.Type[state]) {
                return [this.Type[state], lexem]
            } else {
                return [lexem, lexem]
            }
        } else {
            return [EOF, EOF];
        }
    }

    getToken() {
        const tokens = [];
        while (true) {
            const token = this.nextWord();
            if (token[0] === EOF && token[1] === EOF) {
                break;
            }
            if (token[0] !== "whitespace") {
                tokens.push(token);
            }
        }
        return new Token(tokens);
    }
}
export { Lexer, Token };


// const dfa = DFA.load("./input/Lexer/Expr_dfa.txt");
// const config = JSON.parse(fs.readFileSync("./input/Lexer/Expr_config.json", "utf8"));
// const dfa = DFA.load("./input/Lexer/C_DFA.txt");
// const config = JSON.parse(fs.readFileSync("./input/Lexer/C_config.json", "utf8"));

// const lexer = new Lexer(dfa, config);
// console.table([lexer.S, lexer.s0, lexer.delta, lexer.A]);
// console.log(lexer);
// lexer.analyze('(2 + 3) * a / b + 1');
// console.log(lexer.getToken().tokens);
