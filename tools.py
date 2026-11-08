from langchain.tools import tool
import pymysql
from pydantic import BaseModel,Field
from safe_sql import validate_readonly

@tool
def schema_search():
    '''
    返回当前sql数据库的所有表
    '''
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='123456',
            database='mydb',
            port=3306
        )
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES FROM mydb;")
        tables = cursor.fetchall()
        table_list = [table[0] for table in tables]
        conn.close()
        return table_list
    except Exception as e:
        return f"Error: {str(e)}"

class SqlInstruct(BaseModel):
    instruct: str = Field(description="输入的sql指令，仅限查询")

@tool(args_schema=SqlInstruct)
def sql_query(instruct: str):
    '''
    执行sql查询指令，返回查询结果
    '''
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='123456',
            database='mydb',
            port=3306
        )
        cmd = validate_readonly(instruct)
        cursor = conn.cursor()
        cursor.execute(cmd)
        results = cursor.fetchall()
        conn.close()
        return results
    except Exception as e:
        return f"Error: {str(e)}"

tools = [schema_search, sql_query]
if __name__ == "__main__":
    res = sql_query.invoke({'instruct': "WITH d AS (DELETE FROM employees RETURNING *) SELECT * FROM d;"})
    print(res)