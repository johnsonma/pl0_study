# symbol_table.py
"""
PL/0 符号表和语义分析
管理标识符的作用域和类型信息
"""

from enum import Enum
from typing import Optional, Dict, List, Any

class SymbolType(Enum):
    """符号类型"""
    CONSTANT = "CONSTANT"
    VARIABLE = "VARIABLE"
    PROCEDURE = "PROCEDURE"

class Symbol:
    """符号表条目"""
    
    def __init__(self, 
                 name: str, 
                 symbol_type: SymbolType, 
                 level: int = 0, 
                 value: Any = None,
                 address: int = 0,
                 size: int = 0):
        """
        初始化符号
        
        Args:
            name: 符号名称
            symbol_type: 符号类型
            level: 嵌套层级（0为全局）
            value: 常量值或过程参数个数
            address: 内存地址或过程入口地址
            size: 数组大小或参数个数
        """
        self.name = name
        self.type = symbol_type
        self.level = level  # 嵌套深度
        self.value = value  # 对于常量是值，对于过程是参数个数
        
        # 代码生成相关
        self.address = address  # 对于变量是偏移地址，对于过程是入口地址
        self.size = size  # 对于数组是大小
        
        # 类型检查相关（PL/0简单，可扩展）
        self.data_type = "INTEGER"  # PL/0只有整数
        
        # 链接信息（用于链式符号表）
        self.next: Optional['Symbol'] = None
    
    def __repr__(self):
        if self.type == SymbolType.CONSTANT:
            return f"Constant({self.name}={self.value}, level={self.level})"
        elif self.type == SymbolType.VARIABLE:
            return f"Variable({self.name}, addr={self.address}, level={self.level})"
        else:
            return f"Procedure({self.name}, entry={self.address}, level={self.level}, params={self.value})"

class Scope:
    """作用域"""
    
    def __init__(self, level: int, parent: Optional['Scope'] = None):
        self.level = level
        self.parent = parent
        self.symbols: Dict[str, Symbol] = {}
        self.local_address = 0  # 局部变量偏移
        self.temp_count = 0     # 临时变量计数
    
    def add_symbol(self, symbol: Symbol) -> bool:
        """在当前作用域添加符号"""
        if symbol.name in self.symbols:
            return False  # 重复定义
        
        # 设置地址
        if symbol.type == SymbolType.VARIABLE:
            symbol.address = self.local_address
            self.local_address += 1
        
        self.symbols[symbol.name] = symbol
        return True
    
    def lookup(self, name: str, current_only: bool = False) -> Optional[Symbol]:
        """查找符号"""
        # 在当前作用域查找
        if name in self.symbols:
            return self.symbols[name]
        
        # 如果不在当前作用域且不限制在当前作用域，则向上查找
        if not current_only and self.parent:
            return self.parent.lookup(name)
        
        return None
    
    def get_local_vars_count(self) -> int:
        """获取局部变量数量"""
        count = 0
        for symbol in self.symbols.values():
            if symbol.type == SymbolType.VARIABLE:
                count += 1
        return count
    
    def __repr__(self):
        symbols_str = "\n  ".join(str(sym) for sym in self.symbols.values())
        return f"Scope(level={self.level}, symbols=\n  {symbols_str}\n)"

class SymbolTable:
    """符号表管理器"""
    
    def __init__(self):
        self.current_scope: Optional[Scope] = None
        self.scope_stack: List[Scope] = []
        self.global_scope: Optional[Scope] = None
        
        # 代码生成相关
        self.next_proc_address = 0  # 下一个过程的入口地址
        self.next_temp_index = 0    # 临时变量索引
    
    def enter_scope(self, proc_name: str = "") -> Scope:
        """进入新的作用域"""
        level = 0 if not self.current_scope else self.current_scope.level + 1
        new_scope = Scope(level, self.current_scope)
        
        # 如果是过程作用域，添加过程符号到父作用域
        if proc_name and self.current_scope:
            proc_symbol = Symbol(
                name=proc_name,
                symbol_type=SymbolType.PROCEDURE,
                level=self.current_scope.level,
                value=0,  # 参数个数（PL/0无参数）
                address=self.next_proc_address
            )
            self.current_scope.add_symbol(proc_symbol)
            self.next_proc_address += 1
        
        self.current_scope = new_scope
        self.scope_stack.append(new_scope)
        
        # 如果是第一个作用域，设置为全局作用域
        if level == 0:
            self.global_scope = new_scope
        
        return new_scope
    
    def exit_scope(self) -> Optional[Scope]:
        """退出当前作用域"""
        if len(self.scope_stack) > 1:
            old_scope = self.scope_stack.pop()
            self.current_scope = self.scope_stack[-1]
            return old_scope
        return None
    
    def add_constant(self, name: str, value: int) -> bool:
        """添加常量"""
        if not self.current_scope:
            return False
        
        constant = Symbol(
            name=name,
            symbol_type=SymbolType.CONSTANT,
            level=self.current_scope.level,
            value=value
        )
        return self.current_scope.add_symbol(constant)
    
    def add_variable(self, name: str) -> bool:
        """添加变量"""
        if not self.current_scope:
            return False
        
        variable = Symbol(
            name=name,
            symbol_type=SymbolType.VARIABLE,
            level=self.current_scope.level
        )
        return self.current_scope.add_symbol(variable)
    
    def add_procedure(self, name: str) -> bool:
        """添加过程声明"""
        # 过程符号已在enter_scope时添加
        # 这里主要确保名称在父作用域中可用
        if not self.current_scope:
            return False
        
        # 检查是否与父作用域中的符号重名
        if self.current_scope.parent:
            existing = self.current_scope.parent.lookup(name, current_only=True)
            if existing:
                return False
        
        return True
    
    def lookup(self, name: str) -> Optional[Symbol]:
        """查找符号（从当前作用域向外）"""
        if not self.current_scope:
            return None
        return self.current_scope.lookup(name)
    
    def lookup_current(self, name: str) -> Optional[Symbol]:
        """仅在当前作用域查找"""
        if not self.current_scope:
            return None
        return self.current_scope.lookup(name, current_only=True)
    
    def generate_temp_var(self) -> str:
        """生成临时变量名"""
        temp_name = f"__temp{self.next_temp_index}"
        self.next_temp_index += 1
        self.add_variable(temp_name)
        return temp_name
    
    def get_all_symbols(self) -> List[Symbol]:
        """获取所有符号（用于调试）"""
        all_symbols = []
        for scope in self.scope_stack:
            all_symbols.extend(scope.symbols.values())
        return all_symbols
    
    def print_symbol_table(self):
        """打印符号表"""
        print("=" * 80)
        print("SYMBOL TABLE:")
        print("=" * 80)
        
        for i, scope in enumerate(self.scope_stack):
            print(f"\nScope #{i} (Level {scope.level}):")
            print("-" * 60)
            
            if not scope.symbols:
                print("  (empty)")
                continue
            
            # 按类型分组显示
            constants = [s for s in scope.symbols.values() if s.type == SymbolType.CONSTANT]
            variables = [s for s in scope.symbols.values() if s.type == SymbolType.VARIABLE]
            procedures = [s for s in scope.symbols.values() if s.type == SymbolType.PROCEDURE]
            
            if constants:
                print("  CONSTANTS:")
                for sym in constants:
                    print(f"    {sym.name} = {sym.value}")
            
            if variables:
                print("  VARIABLES:")
                for sym in variables:
                    print(f"    {sym.name} [addr={sym.address}]")
            
            if procedures:
                print("  PROCEDURES:")
                for sym in procedures:
                    print(f"    {sym.name} [entry={sym.address}, level={sym.level}]")
        
        print("=" * 80)

# 语义分析错误
class SemanticError(Exception):
    """语义分析错误"""
    pass

# 语义分析器
class SemanticAnalyzer:
    """PL/0语义分析器"""
    
    def __init__(self, symbol_table: SymbolTable):
        self.symtab = symbol_table
    
    def check_identifier_declared(self, name: str, line: int, col: int):
        """检查标识符是否已声明"""
        symbol = self.symtab.lookup(name)
        if not symbol:
            raise SemanticError(f"Identifier '{name}' not declared at line {line}, col {col}")
        return symbol
    
    def check_variable(self, name: str, line: int, col: int):
        """检查标识符是否为变量"""
        symbol = self.check_identifier_declared(name, line, col)
        if symbol.type != SymbolType.VARIABLE:
            raise SemanticError(f"'{name}' is not a variable at line {line}, col {col}")
        return symbol
    
    def check_procedure(self, name: str, line: int, col: int):
        """检查标识符是否为过程"""
        symbol = self.check_identifier_declared(name, line, col)
        if symbol.type != SymbolType.PROCEDURE:
            raise SemanticError(f"'{name}' is not a procedure at line {line}, col {col}")
        return symbol
    
    def check_constant(self, name: str, line: int, col: int):
        """检查标识符是否为常量"""
        symbol = self.check_identifier_declared(name, line, col)
        if symbol.type != SymbolType.CONSTANT:
            raise SemanticError(f"'{name}' is not a constant at line {line}, col {col}")
        return symbol

# 测试符号表
def test_symbol_table():
    """测试符号表功能"""
    symtab = SymbolTable()
    
    # 进入全局作用域
    symtab.enter_scope("global")
    
    # 添加全局常量
    symtab.add_constant("MAX", 100)
    symtab.add_constant("MIN", 0)
    
    # 添加全局变量
    symtab.add_variable("x")
    symtab.add_variable("y")
    symtab.add_variable("sum")
    
    # 进入过程作用域
    symtab.enter_scope("calculate")
    
    # 添加局部变量
    symtab.add_variable("i")
    symtab.add_variable("temp")
    
    # 添加局部常量
    symtab.add_constant("STEP", 1)
    
    # 生成临时变量
    temp1 = symtab.generate_temp_var()
    temp2 = symtab.generate_temp_var()
    
    # 查找测试
    print("查找测试:")
    print(f"查找 'MAX': {symtab.lookup('MAX')}")
    print(f"查找 'i': {symtab.lookup('i')}")
    print(f"查找 'x' (在过程中): {symtab.lookup('x')}")
    print(f"查找 'nonexistent': {symtab.lookup('nonexistent')}")
    
    # 重复定义测试
    print(f"\n重复定义 'i': {symtab.add_variable('i')} (应为False)")
    
    # 打印符号表
    symtab.print_symbol_table()
    
    # 退出过程作用域
    print("\n退出过程作用域...")
    symtab.exit_scope()
    
    # 进入另一个过程
    symtab.enter_scope("print_results")
    symtab.add_variable("result")
    
    print("\n进入新过程后的符号表:")
    symtab.print_symbol_table()
    
    # 清理
    symtab.exit_scope()
    symtab.exit_scope()

if __name__ == "__main__":
    print("=" * 80)
    print("符号表管理器测试")
    print("=" * 80)
    
    # 运行简单测试
    test_symbol_table()
