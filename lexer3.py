from enum import Enum, auto

# 定义Token类型
class TokenType(Enum):
    INTEGER = auto()
    FLOAT = auto()
    IDENTIFIER = auto()
    OPERATOR = auto()
    KEYWORD = auto()
    WHITESPACE = auto()
    EOF = auto()
    UNKNOWN = auto()

# 定义Token类
class Token:
    def __init__(self, type_, value, line, column):
        self.type = type_
        self.value = value
        self.line = line
        self.column = column
    
    def __repr__(self):
        return f"Token({self.type}, '{self.value}', {self.line}, {self.column})"

# 状态枚举
class State(Enum):
    START = auto()
    IN_INTEGER = auto()
    IN_FLOAT = auto()
    IN_IDENTIFIER = auto()
    IN_OPERATOR = auto()
    IN_WHITESPACE = auto()
    ERROR = auto()

# 字符分类函数
def classify_char(c):
    if c.isdigit():
        return 'digit'
    elif c == '.':
        return 'dot'
    elif c.isalpha() or c == '_':
        return 'alpha'
    elif c in '+-*/=<>!':
        return 'operator'
    elif c.isspace():
        return 'whitespace'
    elif c == '':
        return 'eof'
    else:
        return 'other'

# 关键字集合
KEYWORDS = {'if', 'else', 'while', 'for', 'return', 'int', 'float'}

# 状态转换表
transition_table = {
    State.START: {
        'digit': State.IN_INTEGER,
        'alpha': State.IN_IDENTIFIER,
        'operator': State.IN_OPERATOR,
        'whitespace': State.IN_WHITESPACE,
        'dot': State.ERROR,
        'other': State.ERROR,
        'eof': State.ERROR
    },
    State.IN_INTEGER: {
        'digit': State.IN_INTEGER,
        'dot': State.IN_FLOAT,
        'alpha': State.ERROR,
        'operator': State.START,
        'whitespace': State.START,
        'other': State.ERROR,
        'eof': State.START
    },
    State.IN_FLOAT: {
        'digit': State.IN_FLOAT,
        'dot': State.ERROR,
        'alpha': State.ERROR,
        'operator': State.START,
        'whitespace': State.START,
        'other': State.ERROR,
        'eof': State.START
    },
    State.IN_IDENTIFIER: {
        'digit': State.IN_IDENTIFIER,
        'alpha': State.IN_IDENTIFIER,
        'operator': State.START,
        'whitespace': State.START,
        'dot': State.ERROR,
        'other': State.ERROR,
        'eof': State.START
    },
    State.IN_OPERATOR: {
        'digit': State.START,
        'alpha': State.START,
        'operator': State.IN_OPERATOR,
        'whitespace': State.START,
        'dot': State.START,
        'other': State.ERROR,
        'eof': State.START
    },
    State.IN_WHITESPACE: {
        'digit': State.START,
        'alpha': State.START,
        'operator': State.START,
        'whitespace': State.IN_WHITESPACE,
        'dot': State.START,
        'other': State.ERROR,
        'eof': State.START
    }
}

# 词法分析器类
class Lexer:
    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.line = 1
        self.column = 1
        self.current_char = self.text[self.pos] if self.pos < len(self.text) else ''
    
    def advance(self):
        if self.current_char == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        
        self.pos += 1
        if self.pos < len(self.text):
            self.current_char = self.text[self.pos]
        else:
            self.current_char = ''
    
    def get_next_token(self):
        state = State.START
        lexeme = ''
        start_line = self.line
        start_column = self.column
        
        while True:
            char_class = classify_char(self.current_char)
            
            # 检查是否有状态转换
            if state in transition_table and char_class in transition_table[state]:
                new_state = transition_table[state][char_class]
            else:
                new_state = State.ERROR
            
            # 处理状态转换
            if new_state == State.ERROR:
                if state == State.START:
                    if self.current_char == '':
                        return Token(TokenType.EOF, '', self.line, self.column)
                    else:
                        token = Token(TokenType.UNKNOWN, self.current_char, self.line, self.column)
                        self.advance()
                        return token
                else:
                    # 返回当前识别的token
                    break
            
            # 收集字符
            if state != State.START or new_state != State.START:
                lexeme += self.current_char
            
            state = new_state
            self.advance()
        
        # 确定token类型
        if state == State.IN_INTEGER:
            token_type = TokenType.INTEGER
        elif state == State.IN_FLOAT:
            token_type = TokenType.FLOAT
        elif state == State.IN_IDENTIFIER:
            token_type = TokenType.KEYWORD if lexeme in KEYWORDS else TokenType.IDENTIFIER
        elif state == State.IN_OPERATOR:
            token_type = TokenType.OPERATOR
        elif state == State.IN_WHITESPACE:
            token_type = TokenType.WHITESPACE
        else:
            token_type = TokenType.UNKNOWN
        
        return Token(token_type, lexeme, start_line, start_column)
    
    def tokenize(self):
        tokens = []
        while True:
            token = self.get_next_token()
            tokens.append(token)
            if token.type == TokenType.EOF:
                break
        return [t for t in tokens if t.type != TokenType.WHITESPACE]

# 测试代码
if __name__ == "__main__":
    text = """
    int x = 42;
    float y = 3.14;
    if (x > 10) {
        y = y + 1.0;
    }
    """
    
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    
    for token in tokens:
        print(token)