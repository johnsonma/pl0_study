# parser.py
"""
PL/0 语法分析器（递归下降实现）
根据EBNF文法解析token流
"""

import sys
from typing import List, Optional
from lexer import Lexer, TokenType
from symbol_table import SymbolTable, SymbolType, SemanticAnalyzer, SemanticError

class Parser:
    """PL/0语法分析器（递归下降实现）"""
    
    def __init__(self, lexer: Lexer, symtab: SymbolTable):
        self.lexer = lexer
        self.symtab = symtab
        self.semantic = SemanticAnalyzer(symtab)
        self.tokens = []
        self.current_token_index = 0
        self.errors = []
    
    def parse(self, source_code: str):
        """解析PL/0源代码"""
        # 词法分析
        self.tokens = self.lexer.tokenize()
        self.current_token_index = 0
        self.errors = []
        
        try:
            # 进入全局作用域
            self.symtab.enter_scope("program")
            
            # 解析程序
            self.parse_program()
            
            # 检查是否有未消耗的token
            token = self.current_token()
            if token and token.type != TokenType.EOF:
                self.error(f"Unexpected token at end of program: {token}")
            
            if not self.errors:
                print("✓ 语法分析完成")
            else:
                print(f"\n语法分析完成，发现 {len(self.errors)} 个错误")
                for error in self.errors:
                    print(f"  {error}")
                
        except (SyntaxError, SemanticError) as e:
            self.errors.append(str(e))
            print(f"\n语法分析错误: {e}")
    
    def current_token(self):
        """获取当前token"""
        if self.current_token_index < len(self.tokens):
            return self.tokens[self.current_token_index]
        return None
    
    def advance(self):
        """前进到下一个token"""
        self.current_token_index += 1
        return self.current_token()
    
    def match(self, expected_type: TokenType, expected_value: str = None): # type: ignore
        """匹配当前token"""
        token = self.current_token()
        if token and token.type == expected_type:
            if expected_value is None or token.value == expected_value:
                self.advance()
                return token
        raise SyntaxError(f"Expected {expected_type}, got {token}")
    
    def error(self, message: str):
        """记录错误"""
        token = self.current_token()
        if token:
            self.errors.append(f"Line {token.line}, Col {token.col}: {message}")
        else:
            self.errors.append(f"EOF: {message}")
    
    # ==================== 递归下降解析方法 ====================
    
    def parse_program(self):
        """解析程序: block ."""
        # 解析block
        self.parse_block()
        
        # 匹配结束符
        self.match(TokenType.PERIOD)
        
        print("✓ 程序解析完成")
    
    def parse_block(self):
        """解析块: [const] [var] {procedure} statement"""
        token = self.current_token()
        if not token:
            self.error("Unexpected EOF in block")
            return
            
        # 解析常量声明
        if token.type == TokenType.CONST:
            self.parse_const_declaration()
        
        token = self.current_token()
        if not token:
            self.error("Unexpected EOF after const declaration")
            return
            
        # 解析变量声明
        if token.type == TokenType.VAR:
            self.parse_var_declaration()
        
        # 解析过程声明
        token = self.current_token()
        while token and token.type == TokenType.PROCEDURE:
            self.parse_procedure_declaration()
            token = self.current_token()
        
        # 解析语句
        self.parse_statement()
    
    def parse_const_declaration(self):
        """解析常量声明: const ident = number {, ident = number} ;"""
        self.match(TokenType.CONST)
        
        while True:
            # 获取标识符
            ident_token = self.match(TokenType.IDENT)
            self.match(TokenType.EQ)
            
            # 获取数值
            num_token = self.match(TokenType.NUMBER)
            const_value = int(num_token.value)
            
            # 添加到符号表
            if not self.symtab.add_constant(ident_token.value, const_value):
                self.error(f"Duplicate constant definition: '{ident_token.value}'")
            
            # 检查是否还有更多常量
            token = self.current_token()
            if not token or token.type != TokenType.COMMA:
                break
            self.match(TokenType.COMMA)
        
        self.match(TokenType.SEMICOLON)
        print("✓ 常量声明解析完成")
    
    def parse_var_declaration(self):
        """解析变量声明: var ident {, ident} ;"""
        self.match(TokenType.VAR)
        
        while True:
            # 获取标识符
            ident_token = self.match(TokenType.IDENT)
            
            # 添加到符号表
            if not self.symtab.add_variable(ident_token.value):
                self.error(f"Duplicate variable definition: '{ident_token.value}'")
            
            # 检查是否还有更多变量
            token = self.current_token()
            if not token or token.type != TokenType.COMMA:
                break
            self.match(TokenType.COMMA)
        
        self.match(TokenType.SEMICOLON)
        print("✓ 变量声明解析完成")
    
    def parse_procedure_declaration(self):
        """解析过程声明: procedure ident ; block ;"""
        self.match(TokenType.PROCEDURE)
        
        # 获取过程名
        ident_token = self.match(TokenType.IDENT)
        proc_name = ident_token.value
        
        self.match(TokenType.SEMICOLON)
        
        # 进入过程作用域
        self.symtab.enter_scope(proc_name)
        
        # 解析过程体
        self.parse_block()
        
        # 退出过程作用域
        self.symtab.exit_scope()
        
        self.match(TokenType.SEMICOLON)
        print(f"✓ 过程 '{proc_name}' 解析完成")
    
    def parse_statement(self):
        """解析语句"""
        token = self.current_token()
        if not token:
            return  # 空语句
            
        if token.type == TokenType.IDENT:
            # 赋值语句
            self.parse_assignment()
        elif token.type == TokenType.CALL:
            # 过程调用
            self.parse_procedure_call()
        elif token.type == TokenType.BEGIN:
            # 复合语句
            self.parse_compound_statement()
        elif token.type == TokenType.IF:
            # 条件语句
            self.parse_if_statement()
        elif token.type == TokenType.WHILE:
            # 循环语句
            self.parse_while_statement()
        elif token.type == TokenType.READ:
            # 读语句
            self.parse_read_statement()
        elif token.type == TokenType.WRITE:
            # 写语句
            self.parse_write_statement()
        else:
            # 空语句
            pass
    
    def parse_assignment(self):
        """解析赋值语句: ident := expression"""
        ident_token = self.match(TokenType.IDENT)
        
        # 语义检查：标识符必须是已声明的变量
        try:
            self.semantic.check_variable(ident_token.value, ident_token.line, ident_token.col)
        except SemanticError as e:
            self.error(str(e))
        
        self.match(TokenType.ASSIGN)
        self.parse_expression()
    
    def parse_procedure_call(self):
        """解析过程调用: call ident"""
        self.match(TokenType.CALL)
        ident_token = self.match(TokenType.IDENT)
        
        # 语义检查：标识符必须是已声明的过程
        try:
            self.semantic.check_procedure(ident_token.value, ident_token.line, ident_token.col)
        except SemanticError as e:
            self.error(str(e))
    
    def parse_compound_statement(self):
        """解析复合语句: begin statement {; statement} end"""
        self.match(TokenType.BEGIN)
        
        self.parse_statement()
        
        token = self.current_token()
        while token and token.type == TokenType.SEMICOLON:
            self.match(TokenType.SEMICOLON)
            self.parse_statement()
            token = self.current_token()
        
        self.match(TokenType.END)
    
    def parse_if_statement(self):
        """解析条件语句: if condition then statement [else statement]"""
        self.match(TokenType.IF)
        self.parse_condition()
        self.match(TokenType.THEN)
        self.parse_statement()
        
        # 可选的 else 子句
        token = self.current_token()
        if token and token.type == TokenType.ELSE:
            self.match(TokenType.ELSE)
            self.parse_statement()
    
    def parse_while_statement(self):
        """解析循环语句: while condition do statement"""
        self.match(TokenType.WHILE)
        self.parse_condition()
        self.match(TokenType.DO)
        self.parse_statement()
    
    def parse_read_statement(self):
        """解析读语句: read ident"""
        self.match(TokenType.READ)
        ident_token = self.match(TokenType.IDENT)
        
        # 语义检查：标识符必须是已声明的变量
        try:
            self.semantic.check_variable(ident_token.value, ident_token.line, ident_token.col)
        except SemanticError as e:
            self.error(str(e))
    
    def parse_write_statement(self):
        """解析写语句: write expression"""
        self.match(TokenType.WRITE)
        self.parse_expression()
    
    def parse_condition(self):
        """解析条件"""
        token = self.current_token()
        if not token:
            self.error("Unexpected EOF in condition")
            return
            
        if token.type == TokenType.ODD:
            self.match(TokenType.ODD)
            self.parse_expression()
        else:
            self.parse_expression()
            
            # 关系运算符
            rel_op = self.current_token()
            if rel_op and rel_op.type in [TokenType.EQ, TokenType.NEQ, TokenType.LT, 
                              TokenType.LE, TokenType.GT, TokenType.GE]:
                self.advance()
                self.parse_expression()
    
    def parse_expression(self):
        """解析表达式"""
        # 可选符号
        token = self.current_token()
        if token and token.type in [TokenType.PLUS, TokenType.MINUS]:
            self.advance()
        
        self.parse_term()
        
        # 加减项
        token = self.current_token()
        while token and token.type in [TokenType.PLUS, TokenType.MINUS]:
            self.advance()
            self.parse_term()
            token = self.current_token()
    
    def parse_term(self):
        """解析项"""
        self.parse_factor()
        
        # 乘除因子
        token = self.current_token()
        while token and token.type in [TokenType.MULTIPLY, TokenType.DIVIDE]:
            self.advance()
            self.parse_factor()
            token = self.current_token()
    
    def parse_factor(self):
        """解析因子"""
        token = self.current_token()
        if not token:
            self.error("Unexpected EOF in factor")
            return
        
        if token.type == TokenType.IDENT:
            self.advance()
            
            # 语义检查：标识符必须已声明
            try:
                self.semantic.check_identifier_declared(token.value, token.line, token.col)
            except SemanticError as e:
                self.error(str(e))
        
        elif token.type == TokenType.NUMBER:
            self.advance()
        
        elif token.type == TokenType.LPAREN:
            self.match(TokenType.LPAREN)
            self.parse_expression()
            self.match(TokenType.RPAREN)
        
        else:
            self.error(f"Unexpected token in factor: {token}")

# 测试语法分析器
def test_parser():
    """测试语法分析器"""
    source_code = """
    { PL/0示例程序: 计算奇数和 }
    const MAX = 100;
    var x, sum;
    
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
    symtab = SymbolTable()
    parser = Parser(lexer, symtab)
    
    print("语法分析测试:")
    print("-" * 40)
    
    parser.parse(source_code)
    
    if not parser.errors:
        print("\n语法分析测试通过!")
        
        # 打印符号表
        print("\n生成的符号表:")
        symtab.print_symbol_table()
        
        return 0
    else:
        print(f"\n语法分析测试失败，发现 {len(parser.errors)} 个错误")
        for error in parser.errors:
            print(f"  {error}")
        return 1

if __name__ == "__main__":
    sys.exit(test_parser())
