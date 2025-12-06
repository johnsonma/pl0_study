# lexer.py
"""
PL/0 词法分析器
将源代码转换为token流
"""

import re
from enum import Enum
from typing import Optional, List, Tuple

class TokenType(Enum):
    """Token类型枚举"""
    # 关键字
    CONST = 'CONST'
    VAR = 'VAR'
    PROCEDURE = 'PROCEDURE'
    CALL = 'CALL'
    BEGIN = 'BEGIN'
    END = 'END'
    IF = 'IF'
    THEN = 'THEN'
    ELSE = 'ELSE'
    WHILE = 'WHILE'
    DO = 'DO'
    READ = 'READ'
    WRITE = 'WRITE'
    ODD = 'ODD'
    
    # 运算符
    ASSIGN = ':='
    EQ = '='
    NEQ = '#'
    LT = '<'
    LE = '<='
    GT = '>'
    GE = '>='
    PLUS = '+'
    MINUS = '-'
    MULTIPLY = '*'
    DIVIDE = '/'
    
    # 分隔符
    SEMICOLON = ';'
    COMMA = ','
    PERIOD = '.'
    LPAREN = '('
    RPAREN = ')'
    
    # 标识符和字面量
    IDENT = 'IDENT'
    NUMBER = 'NUMBER'
    
    # 特殊标记
    EOF = 'EOF'

class Token:
    """Token类，表示一个词法单元"""
    
    def __init__(self, type: TokenType, value: str = '', line: int = 0, col: int = 0):
        self.type = type
        self.value = value
        self.line = line
        self.col = col
    
    def __repr__(self):
        return f'Token({self.type.name}, {repr(self.value)}, line={self.line}, col={self.col})'
    
    def __eq__(self, other):
        if isinstance(other, Token):
            return self.type == other.type and self.value == other.value
        return False

class Lexer:
    """PL/0词法分析器"""
    
    # 关键字映射
    KEYWORDS = {
        'const': TokenType.CONST,
        'var': TokenType.VAR,
        'procedure': TokenType.PROCEDURE,
        'call': TokenType.CALL,
        'begin': TokenType.BEGIN,
        'end': TokenType.END,
        'if': TokenType.IF,
        'then': TokenType.THEN,
        'else': TokenType.ELSE,
        'while': TokenType.WHILE,
        'do': TokenType.DO,
        'read': TokenType.READ,
        'write': TokenType.WRITE,
        'odd': TokenType.ODD,
    }
    
    # 操作符映射（多字符优先）
    OPERATORS = {
        ':=': TokenType.ASSIGN,
        '<=': TokenType.LE,
        '>=': TokenType.GE,
        '=': TokenType.EQ,
        '#': TokenType.NEQ,
        '<': TokenType.LT,
        '>': TokenType.GT,
        '+': TokenType.PLUS,
        '-': TokenType.MINUS,
        '*': TokenType.MULTIPLY,
        '/': TokenType.DIVIDE,
    }
    
    # 分隔符映射
    DELIMITERS = {
        ';': TokenType.SEMICOLON,
        ',': TokenType.COMMA,
        '.': TokenType.PERIOD,
        '(': TokenType.LPAREN,
        ')': TokenType.RPAREN,
    }
    
    def __init__(self, source_code: str):
        self.source = source_code
        self.position = 0
        self.line = 1
        self.column = 1
        self.current_char = self.source[0] if source_code else None
        self.tokens = []
    
    def advance(self):
        """移动位置指针"""
        if self.current_char == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
            
        self.position += 1
        if self.position < len(self.source):
            self.current_char = self.source[self.position]
        else:
            self.current_char = None
    
    def peek(self, n: int = 1) -> Optional[str]:
        """预览后续字符"""
        pos = self.position + n
        if pos < len(self.source):
            return self.source[pos]
        return None
    
    def skip_whitespace(self):
        """跳过空白字符"""
        while self.current_char and self.current_char.isspace():
            self.advance()
    
    def skip_comment(self):
        """跳过注释 { ... }"""
        if self.current_char == '{':
            self.advance()  # 跳过 {
            while self.current_char and self.current_char != '}':
                self.advance()
            if self.current_char == '}':
                self.advance()  # 跳过 }
            else:
                raise SyntaxError(f"Unterminated comment at line {self.line}")
    
    def read_number(self) -> Token:
        """读取数字"""
        start_col = self.column
        result = ''
        while self.current_char and self.current_char.isdigit():
            result += self.current_char
            self.advance()
        
        # 检查是否为浮点数（PL/0不支持，这里为了健壮性）
        if self.current_char == '.':
            result += self.current_char
            self.advance()
            while self.current_char and self.current_char.isdigit():
                result += self.current_char
                self.advance()
        
        return Token(TokenType.NUMBER, result, self.line, start_col)
    
    def read_identifier(self) -> Token:
        """读取标识符或关键字"""
        start_col = self.column
        result = ''
        while self.current_char and (self.current_char.isalnum() or self.current_char == '_'):
            result += self.current_char
            self.advance()
        
        # 检查是否为关键字
        token_type = self.KEYWORDS.get(result.lower())
        if token_type:
            return Token(token_type, result.lower(), self.line, start_col)
        else:
            return Token(TokenType.IDENT, result, self.line, start_col)
    
    def read_operator(self) -> Token:
        """读取操作符（支持多字符）"""
        start_col = self.column
        
        if not self.current_char:
            raise SyntaxError(f"Unexpected EOF at line {self.line}, col {start_col}")
        
        # 尝试读取两字符操作符
        next_char = self.peek() or ''
        two_char = self.current_char + next_char
        if two_char in self.OPERATORS:
            token_type = self.OPERATORS[two_char]
            self.advance()  # 跳过第一个字符
            if next_char:  # 如果还有第二个字符
                self.advance()  # 跳过第二个字符
            return Token(token_type, two_char, self.line, start_col)
        
        # 尝试读取单字符操作符
        one_char = self.current_char
        if one_char in self.OPERATORS:
            token_type = self.OPERATORS[one_char]
            self.advance()
            return Token(token_type, one_char, self.line, start_col)
        
        raise SyntaxError(f"Unknown operator '{one_char}' at line {self.line}, col {start_col}")
    
    def get_next_token(self) -> Token:
        """获取下一个token"""
        while self.current_char:
            # 跳过空白
            if self.current_char.isspace():
                self.skip_whitespace()
                continue
            
            # 跳过注释
            if self.current_char == '{':
                self.skip_comment()
                continue
            
            # 标识符或关键字
            if self.current_char.isalpha() or self.current_char == '_':
                return self.read_identifier()
            
            # 数字
            if self.current_char.isdigit():
                return self.read_number()
            
            # 操作符
            if self.current_char in ':=#<>+-*/':
                return self.read_operator()
            
            # 分隔符
            if self.current_char in ';,.()':
                delim = self.current_char
                token_type = self.DELIMITERS[delim]
                start_col = self.column
                self.advance()
                return Token(token_type, delim, self.line, start_col)
            
            # 未知字符
            raise SyntaxError(f"Unknown character '{self.current_char}' at line {self.line}, col {self.column}")
        
        # 文件结束
        return Token(TokenType.EOF, '', self.line, self.column)
    
    def tokenize(self) -> List[Token]:
        """将源代码转换为token流"""
        tokens = []
        while True:
            token = self.get_next_token()
            tokens.append(token)
            if token.type == TokenType.EOF:
                break
        return tokens
    
    def pretty_print_tokens(self):
        """格式化输出token流"""
        print("=" * 80)
        print("TOKEN STREAM:")
        print("=" * 80)
        print(f"{'LINE':<5} {'COL':<5} {'TYPE':<15} {'VALUE':<20}")
        print("-" * 80)
        
        for token in self.tokens:
            if token.type != TokenType.EOF:
                print(f"{token.line:<5} {token.col:<5} {token.type.value:<15} {repr(token.value):<20}")
        
        print("=" * 80)

# 测试词法分析器
def test_lexer():
    """测试词法分析器"""
    source_code = """
    { 这是一个PL/0程序示例 }
    const MAX = 100;
    var x, y, sum;
    
    procedure calculate;
    begin
        sum := 0;
        read(x);
        while x > 0 do
        begin
            if odd(x) then
                sum := sum + x;
            read(x)
        end;
        write(sum)
    end;
    
    call calculate.
    """
    
    lexer = Lexer(source_code)
    tokens = lexer.tokenize()
    
    print("词法分析测试:")
    print("-" * 40)
    for i, token in enumerate(tokens[:100]):  # 只显示前20个token
        print(f"{i:3}: {token}")
    
    # 统计信息
    ident_count = sum(1 for t in tokens if t.type == TokenType.IDENT)
    num_count = sum(1 for t in tokens if t.type == TokenType.NUMBER)
    print(f"\n统计: {len(tokens)} tokens, {ident_count} 标识符, {num_count} 数字")

if __name__ == "__main__":
    test_lexer()
