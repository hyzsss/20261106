import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError

# 定义允许的“只读”语句类型
ALLOWED_TYPES = (exp.Select, exp.Union, exp.Intersect, exp.Except)

# 定义即使在 SELECT 内部也不允许出现的危险节点
FORBIDDEN_NODES = (
    exp.Insert, exp.Update, exp.Delete, exp.Merge, exp.Create, exp.Alter, exp.Drop,
    exp.Into,    # 对应 SELECT ... INTO OUTFILE 等
)

def validate_readonly(sql: str, dialect: str = "mysql") -> str:
    """
    校验 SQL 是否为安全的只读查询。
    返回规范化后的 SQL 字符串；若不安全则抛出 ValueError。
    """
    if not sql or not sql.strip():
        raise ValueError("SQL 不能为空")

    try:
        # 1. 解析：将 SQL 字符串转为 AST 列表
        statements = sqlglot.parse(sql, read=dialect)
    except ParseError as e:
        raise ValueError(f"SQL 语法解析失败: {e}")

    # 过滤掉 None（空语句）
    statements = [s for s in statements if s is not None]
    if not statements:
        raise ValueError("未解析到有效 SQL 语句")

    # 2. 禁止多语句：防止 SELECT 1; DROP TABLE ...
    if len(statements) > 1:
        raise ValueError("不允许执行多条语句")

    stmt = statements[0]

    # 3. 检查根节点类型：必须是 SELECT 或集合操作
    if not isinstance(stmt, ALLOWED_TYPES):
        raise ValueError(f"仅允许查询语句，检测到: {type(stmt).__name__}")

    # 4. 深度遍历 AST：检查是否存在隐藏的危险操作（如 CTE 中的 DELETE、SELECT INTO）
    for node in stmt.walk():
        # node 可能是元组或单个节点，需根据 sqlglot 版本处理
        # 这里用 find_all 更直接：
        pass

    # 使用 find_all 深度查找危险节点
    for forbidden_type in FORBIDDEN_NODES:
        if stmt.find(forbidden_type):
            raise ValueError(f"查询中包含不允许的操作: {forbidden_type.__name__}")

    # 通过校验，返回规范化后的 SQL
    return stmt.sql(dialect=dialect)