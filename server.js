import express from 'express';
import bodyParser from 'body-parser';
import path from 'path';
import fs from 'fs';
import { FA, NFA, DFA } from './utils/FA.js';
import { Grammar } from './utils/Grammar.js';
import DotRender from './utils/DotRender.js';
import { Lexer, Token } from './utils/Lexer.js';
const app = express();
const dotRender = new DotRender();
const port = 8086;

app.use(express.static('public'));
app.use(bodyParser.json());

// const rootPath = process.env.ROOT_PATH || path.resolve(new URL('.', import.meta.url).pathname, './');
const rootPath = './';

const inputPath = path.join(rootPath, 'input');
const tempPath = path.join(rootPath, 'temp');

console.log(rootPath);

app.get('/api/lexical/fa/list', (req, res) => {
    try {
        const FAList = JSON.parse(fs.readFileSync(path.join(inputPath, 'default.json'), 'utf-8')).FA;
        const data = {};
        FAList.forEach(name => {
            const fa = fs.readFileSync(path.join(inputPath, 'FA', `${name}_FA.txt`), 'utf-8');
            data[name] = { fa };
        });
        res.json(data);
    } catch (error) {
        console.error('获取预设FA失败:', error.stack);
        res.status(400).json({ error: error.message });
    }
});


/**
 * 词法分析：加载FA
 */
app.post('/api/lexical/fa/load', (req, res) => {
    try {
        const { faInput } = req.body;
        const tempFile = path.join(tempPath, 'temp_fa.txt');
        fs.writeFileSync(tempFile, faInput);
        let fa = null;
        try {
            fa = FA.load(tempFile);
        } catch (error) {
            throw new Error("输入的NFA有误");
        }
        fs.unlinkSync(tempFile);
        res.json({
            S: fa.S,
            sigma: fa.sigma,
            delta: fa.delta,
            s0: fa.s0,
            A: fa.A
        });
    } catch (error) {
        console.error('加载FA过程中出错：', error.stack);
        res.status(400).json({ error: error.message });
    }
});

/**
 * 词法分析：导出dot
 */
app.post('/api/lexical/fa/dot', (req, res) => {
    try {
        const { data } = req.body;
        const fa = new FA(data.S, data.sigma, data.delta, data.s0, data.A);
        const dotSource = fa.dot();
        res.json({ dotSource: dotSource });
    } catch (error) {
        console.error('导出 dot 过程中出错：', error.stack);
        res.status(400).json({ error: error.message });
    }
});

/**
 * 词法分析：FA渲染svg
 */
app.post('/api/lexical/fa/render', async (req, res) => {
    try {
        const { dotSource } = req.body;
        const svgContent = await dotRender.render(dotSource);
        res.json({ svg: svgContent });
    } catch (error) {
        console.error('渲染 dot 失败：', error.stack);
        res.status(400).json({ error: error.message });
    }
});

/**
 * 词法分析：转换FA
 */
app.post('/api/lexical/fa/convert', (req, res) => {
    try {
        const { nfaInput } = req.body;
        // 创建临时文件
        const tempFile = path.join(tempPath, 'temp_nfa.txt');
        // 将NFA输入保存到临时文件
        fs.writeFileSync(tempFile, nfaInput);
        // 创建NFA并进行转换
        const nfa = NFA.load(tempFile);
        const [dfa, Q, T] = nfa.subsetConstruction();
        const [minDfa, PI] = dfa.hopcroft();
        // 清理临时文件
        fs.unlinkSync(tempFile);

        // 返回转换结果
        res.json({
            nfa: {
                S: nfa.S,
                sigma: nfa.sigma,
                delta: nfa.delta,
                s0: nfa.s0,
                A: nfa.A
            },
            dfa: {
                S: dfa.S,
                sigma: dfa.sigma,
                delta: dfa.delta,
                s0: dfa.s0,
                A: dfa.A,
                Q: Q,
                T: T
            },
            minDfa: {
                S: minDfa.S,
                sigma: minDfa.sigma,
                delta: minDfa.delta,
                s0: minDfa.s0,
                A: minDfa.A,
                PI: PI
            }
        });
    } catch (error) {
        console.error('转换FA过程中出错：', error.stack);
        res.status(400).json({ error: error.message });
    }
});

/** 
 * 获取预设的词法分析器
 */
app.get('/api/lexical/lexer/list', (req, res) => {
    try {
        const lexerList = JSON.parse(fs.readFileSync(path.join(inputPath, 'default.json'), 'utf-8')).lexer;
        const data = {};
        lexerList.forEach(name => {
            const dfa = fs.readFileSync(path.join(inputPath, 'Lexer', `${name}_DFA.txt`), 'utf-8');
            const charCat = fs.readFileSync(path.join(inputPath, 'Lexer', `${name}_config.json`), 'utf-8');
            let inputString = "";
            if (fs.existsSync(path.join(inputPath, 'Lexer', `${name}_input.txt`))) {
                inputString = fs.readFileSync(path.join(inputPath, 'Lexer', `${name}_input.txt`), 'utf-8');
            }
            data[name] = { dfa, charCat, inputString };
        });
        res.json(data);
    } catch (error) {
        console.error('获取词法分析器失败:', error.stack);
        res.status(500).json({ error: error.message });
    }
});

let lexer = null;

/**
 * 加载词法分析器
 */
app.post('/api/lexical/lexer/load', (req, res) => {
    try {
        const { dfa, config } = req.body;
        try {
            lexer = new Lexer(dfa, config);
        } catch (error) {
            throw new Error("输入的DFA或配置有误");
        }
        res.json({ message: '词法分析器创建成功' });
    } catch (error) {
        console.error('词法分析器创建失败：:', error.stack);
        res.status(400).json({ error: error.message });
    }
});

/**
 * 对字符流进行词法分析
 */
app.post('/api/lexical/lexer/analyze', (req, res) => {
    try {
        const { inputString } = req.body;
        if (!lexer) {
            throw new Error('词法分析器未加载');
        }
        lexer.analyze(inputString);
        const tokens = lexer.getToken().tokens;
        res.json({ tokens });
    } catch (error) {
        console.error('分析失败：', error.stack);
        res.status(400).json({ error: error.message });
    }
});



/** 
 * 获取预设的词法分析器
 */
app.get('/api/grammar/ll1/list', (req, res) => {
    try {
        const lexerList = JSON.parse(fs.readFileSync(path.join(inputPath, 'default.json'), 'utf-8')).ll1;
        const data = {};
        lexerList.forEach(name => {
            const grammar = fs.readFileSync(path.join(inputPath, 'Grammar', `${name}_G.txt`), 'utf-8');
            let inputStream = "";
            if (fs.existsSync(path.join(inputPath, 'Grammar', `${name}_input.txt`))) {
                inputStream = fs.readFileSync(path.join(inputPath, 'Grammar', `${name}_input.txt`), 'utf-8');
            }
            data[name] = { grammar, inputStream };
        });
        res.json(data);
    } catch (error) {
        console.error('获取LL(1)文法失败:', error.stack);
        res.status(500).json({ error: error.message });
    }
});
let grammar = null;
/**
 * LL(1)语法分析：加载语法规则
 */
app.post('/api/grammar/ll1/load', (req, res) => {
    try {
        const { grammarInput } = req.body;
        const tempFile = path.join(tempPath, 'temp_grammar.txt');
        fs.writeFileSync(tempFile, grammarInput);
        try {
            grammar = Grammar.load(tempFile);
        } catch (error) {
            throw new Error("输入的文法有误");
        }
        fs.unlinkSync(tempFile);
        const Pstr = grammar.Pstr;
        const firstSet = grammar.firstSet();
        const followSet = grammar.followSet();
        const selectSet = grammar.selectSet();
        const ll1Table = grammar.LL1Table();
        res.json({
            NT: grammar.NT,
            T: grammar.T,
            firstSet,
            followSet,
            selectSet,
            ll1Table,
            Pstr
        });
    } catch (error) {
        console.error('加载语法规则失败：', error.stack);
        res.status(400).json({ error: error.message });
    }
});
/**
 * LL(1)语法分析：执行分析
 */
app.post('/api/grammar/ll1/analyze', (req, res) => {
    try {
        const { inputStream } = req.body;
        // 执行LL(1)语法分析
        const tokens = inputStream.split(' ').filter(word => word.trim()).map(word => [word, word]);
        if (grammar === null) {
            throw new Error("未加载文法");
        }
        const LL1JudgeMessage = grammar.isLL1();
        if (LL1JudgeMessage !== "是LL(1)文法") {
            throw new Error(LL1JudgeMessage);
        }
        const [syntaxTree, processList, message] = grammar.LL1analyze(new Token(tokens));
        // 返回分析过程
        res.json({ syntaxTree, processList, message });
    } catch (error) {
        console.error('语法分析失败：', error.stack);
        res.status(400).json({ error: error.message });
    }
});

/**
 * LR(1)语法分析：加载语法规则
 */
app.post('/api/grammar/lr1/load', (req, res) => {
    try {
        const { grammarInput } = req.body;
        const tempFile = path.join(tempPath, 'temp_grammar.txt');
        fs.writeFileSync(tempFile, grammarInput);
        try {
            grammar = Grammar.load(tempFile);
        } catch (error) {
            throw new Error("输入的文法有误");
        }
        fs.unlinkSync(tempFile);
        const Pstr = grammar.Pstr;
        const [CC, CC_dict] = grammar.getCC();
        const dfa = grammar.CC_DFA();
        const [Action, Goto] = grammar.LR1Table();
        res.json({
            NT: grammar.NT,
            T: grammar.T,
            Pstr,
            CC,
            CC_dict,
            dfa,
            Action,
            Goto
        });
    } catch (error) {
        console.error('加载语法规则失败：', error.stack);
        res.status(400).json({ error: error.message });
    }
})

/** 
 * 获取预设的词法分析器
 */
app.get('/api/grammar/lr1/list', (req, res) => {
    try {
        const lexerList = JSON.parse(fs.readFileSync(path.join(inputPath, 'default.json'), 'utf-8')).lr1;
        const data = {};
        lexerList.forEach(name => {
            const grammar = fs.readFileSync(path.join(inputPath, 'Grammar', `${name}_G.txt`), 'utf-8');
            let inputStream = "";
            if (fs.existsSync(path.join(inputPath, 'Grammar', `${name}_input.txt`))) {
                inputStream = fs.readFileSync(path.join(inputPath, 'Grammar', `${name}_input.txt`), 'utf-8');
            }
            data[name] = { grammar, inputStream };
        });
        res.json(data);
    } catch (error) {
        console.error('获取LR(1)文法失败:', error.stack);
        res.status(500).json({ error: error.message });
    }
});

/**
 * LR(1)语法分析：执行分析
 */
app.post('/api/grammar/lr1/analyze', (req, res) => {
    try {
        const { inputStream } = req.body;
        // 执行LR(1)语法分析
        const tokens = inputStream.split(' ').filter(word => word.trim()).map(word => [word, word]);
        if (grammar === null) {
            throw new Error("未加载文法");
        }
        const [syntaxTree, processList, message] = grammar.LR1analyze(new Token(tokens));
        // 返回分析过程
        res.json({ syntaxTree, processList, message });
    } catch (error) {
        console.error('语法分析失败：', error.stack);
        res.status(400).json({ error: error.message });
    }
});

app.listen(port, () => {
    console.log(`Server running at http://localhost:${port}`);
});
