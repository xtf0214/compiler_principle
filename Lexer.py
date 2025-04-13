from enum import Enum


class State(Enum):
    start = 0
    number = 1
    word = 2
    operator = 3
    whitespace = 4
    error = 5


class CharCat(Enum):
    operator = 0
    digit = 1
    alpha = 2
    space = 3
    other = 4


EOF = "$"

class Token:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
    def next_word(self):
        if self.pos >= len(self.tokens):
            return EOF, EOF 
        word = self.tokens[self.pos]
        self.pos += 1
        return word


class Lexer:

    def __init__(self, input_string):
        self.input = input_string + EOF
        self.pos = 0

        self.delta = {
            State.start: {
                CharCat.digit: State.number,
                CharCat.alpha: State.word,
                CharCat.operator: State.operator,
                CharCat.space: State.whitespace,
            },
            State.number: {
                CharCat.digit: State.number,
            },
            State.word: {
                CharCat.digit: State.word,
                CharCat.alpha: State.word,
            },
            State.operator: {},
            State.whitespace: {
                CharCat.space: State.whitespace,
            },
            State.error: {},
        }
        self.type = {
            State.start: "invalid",
            State.number: "num",
            State.word: "name",
            State.operator: "operator",
            State.error: "invalid",
            State.whitespace: "whitespace",
        }
        self.A = [State.number, State.word, State.operator, State.whitespace]

    def next_char(self):
        if self.pos < len(self.input):
            char = self.input[self.pos]
            self.pos += 1
            return char
        return EOF

    def roll_back(self):
        if self.pos > 0:
            self.pos -= 1

    def char_cat(self, char: str):
        if char.isalpha():
            return CharCat.alpha
        elif char.isdigit():
            return CharCat.digit
        elif char in "+-*/()":
            return CharCat.operator
        elif char.isspace():
            return CharCat.space
        else:
            return CharCat.other

    def next_word(self):
        state = State.start
        lexem = ""
        stack = []
        stack.append("bad")
        while state != State.error:
            char = self.next_char()
            lexem += char
            if state in self.A:
                stack.clear()
            stack.append(state)
            cat = self.char_cat(char)
            if cat in self.delta[state]:
                state = self.delta[state][cat]
            else:
                state = State.error
        while state not in self.A and state != "bad":
            state = stack.pop()
            lexem = lexem[:-1]
            self.roll_back()
        if state in self.A:
            if self.type[state] in ["num", "name"]:
                return self.type[state], lexem
            else:
                return lexem, lexem
        else:
            return EOF, EOF

    def get_token(self):
        tokens = []
        while True:
            token = self.next_word()
            print(token)
            if token == (EOF, EOF):
                break
            if token[0] == "whitespace":
                continue
            tokens.append(token)
        return Token(tokens)


if __name__ == "__main__":
    lexer = Lexer("(a5+a8)")
    print(lexer.get_token())
