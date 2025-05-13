import json
from FA import DFA


EOF = "$"


class Token:
    def __init__(self, tokens):
        self.tokens = tokens
        self.types = [type for type, word in tokens]
        self.words = [word for type, word in tokens]
        self.pos = 0

    def next(self):
        if self.pos >= len(self.tokens):
            return EOF, EOF
        word = self.tokens[self.pos]
        self.pos += 1
        return word

    def peek(self):
        if self.pos >= len(self.tokens):
            return EOF, EOF
        word = self.tokens[self.pos]
        return word

    def get_types(self):
        return self.types[: self.pos] + ["↑"] + self.types[self.pos :]


class CharStream:
    def __init__(self, input_string):
        self.input = input_string + EOF
        self.pos = 0

    def has_next(self):
        return self.pos < len(self.input) - 1

    def next_char(self):
        if self.pos < len(self.input):
            char = self.input[self.pos]
            self.pos += 1
            return char
        else:
            self.pos += 1
            return EOF

    def roll_back(self):
        if self.pos > 0:
            self.pos -= 1


class Lexer:

    def __init__(self, dfa: DFA, config: dict):
        self.S = dfa.S
        self.s0 = dfa.s0
        self.sigma = dfa.sigma
        self.delta = {}
        for s, c, t in dfa.delta:
            self.delta.setdefault(s, {}).setdefault(c, t)
        self.A = dfa.A
        self.Type = config["Type"]
        self.charCat = config["charCat"]
        self.keyword = config["keyword"]
        self.char_stream = None

    def analyze(self, input_string):
        self.char_stream = CharStream(input_string)
        return self

    def next_word(self):
        if not self.char_stream.has_next():
            return EOF, EOF
        state = self.s0
        lexem = ""
        stack = []
        stack.append("bad")
        while state != "err":
            char = self.char_stream.next_char()
            lexem += char
            if state in self.A:
                stack.clear()
            stack.append(state)
            try:
                cat = next(filter(lambda x: char in self.charCat[x], self.charCat.keys()))
            except StopIteration:
                cat = "other"
            if state in self.delta and cat in self.delta[state]:
                state = self.delta[state][cat]
            else:
                state = "err"
        while state not in self.A and state != "bad":
            state = stack.pop()
            lexem = lexem[:-1]
            self.char_stream.roll_back()
        if state in self.A:
            if state in self.Type:
                if lexem not in self.keyword:
                    return self.Type[state], lexem
            return lexem, lexem
        else:
            return EOF, EOF

    def get_token(self):
        tokens = []
        while True:
            token = self.next_word()
            if token == (EOF, EOF):
                break
            if token[0] != "whitespace":
                tokens.append(token)
        return Token(tokens)


if __name__ == "__main__":
    # 使用 DFA 、 charCat分类器 和 状态转移表 构造词法分析器
    dfa = DFA.load("./input/Lexer/Expr_DFA.txt")
    with open("./input/Lexer/Expr_config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
    lexer = Lexer(dfa, config)
    lexer.analyze("a + b * c")
    print(lexer.get_token().tokens)


    # dfa = DFA.load("./input/Lexer/C_DFA.txt")
    # with open("./input/Lexer/C_config.json", "r", encoding="utf-8") as f:
    #     config = json.load(f)
    # lexerExpr = Lexer(dfa, config)
    # with open("./input/Lexer/C_input.txt", "r", encoding="utf-8") as f:
    #     input_string = f.read()
    # lexerExpr.analyze(input_string)
    # print(lexerExpr.get_token().tokens)