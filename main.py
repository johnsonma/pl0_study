# main.py
"""
PL/0 编译器主程序
集成词法分析、语法分析和语义分析
"""

import sys
import os
from lexer import Lexer
from symbol_table import SymbolTable
from parser import Parser

class PL0Compiler:
    """PL/0编译器主程序"""
    
    def __init__(self):
        self.lexer = None
        self.symtab = SymbolTable()
        self.parser = None
    
    def compile(self, source_code: str, source_file: str = ""):
        """编译PL/0源代码"""
        print("=" * 80)
        if source_file:
            print(f"编译文件: {source_file}")
        else:
            print("编译示例程序")
        print("=" * 80)
        
        # 词法分析
        print("\n阶段1: 词法分析")
        print("-" * 40)
        self.lexer = Lexer(source_code)
        tokens = self.lexer.tokenize()
        
        # 输出token信息
        print(f"生成 {len(tokens)} 个token")
        
        # 可选：显示token流
        if len(tokens) < 50:  # 如果token不多，显示全部
            print("\nToken流:")
            for i, token in enumerate(tokens):
                if token.type != token.type.EOF:
                    print(f"  {i:3}: {token}")
        
        # 语法分析和语义分析
        print("\n阶段2: 语法分析和语义分析")
        print("-" * 40)
        self.parser = Parser(self.lexer, self.symtab)
        self.parser.parse(source_code)
        
        # 输出符号表
        if not self.parser.errors:
            print("\n阶段3: 符号表展示")
            print("-" * 40)
            self.symtab.print_symbol_table()
        
        # 编译结果
        print("\n" + "=" * 80)
        print("编译结果:")
        print("=" * 80)
        
        if not self.parser.errors:
            print("✓ 编译成功！程序语法正确。")
            return True
        else:
            print(f"✗ 编译失败，发现 {len(self.parser.errors)} 个错误")
            return False
    
    def compile_file(self, file_path: str):
        """编译文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            return self.compile(source_code, file_path)
        except FileNotFoundError:
            print(f"错误: 文件 '{file_path}' 不存在")
            return False
        except Exception as e:
            print(f"错误: 读取文件时发生错误: {e}")
            return False

def main():
    """主函数"""
    # 读取命令行参数
    if len(sys.argv) > 1:
        # 编译指定文件
        file_path = sys.argv[1]
        if not os.path.exists(file_path):
            print(f"错误: 文件 '{file_path}' 不存在")
            return 1
        
        compiler = PL0Compiler()
        success = compiler.compile_file(file_path)
        return 0 if success else 1
    else:
        # 使用示例程序
        source_code = """
        { PL/0示例程序: 计算1到10的和 }
        const N = 10;
        var i, sum;
        
        begin
            sum := 0;
            i := 1;
            while i <= N do
            begin
                sum := sum + i;
                i := i + 1
            end;
            write(sum)
        end.
        """
        
        compiler = PL0Compiler()
        success = compiler.compile(source_code)
        return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
