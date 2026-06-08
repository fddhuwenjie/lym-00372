import time
from sqlalchemy import text
from app.database import db
from app.services.sql_generator import SQLGenerator
from app.services.security_service import SecurityService

class QueryExecutor:
    @staticmethod
    def generate_sql(query_structure):
        generator = SQLGenerator(query_structure)
        sql = generator.generate()
        params = generator.get_params()
        return {'sql': sql, 'params': params}
    
    @staticmethod
    def execute(query_structure):
        result = QueryExecutor.generate_sql(query_structure)
        sql = result['sql']
        params = result['params']
        
        start_time = time.time()
        
        try:
            query_result = db.session.execute(text(sql), params)
            
            raw_rows = query_result.fetchall()
            rows = [list(row) for row in raw_rows]
            
            column_names = list(query_result.keys())
            
            columns = []
            for idx, col_name in enumerate(column_names):
                type_name = QueryExecutor._infer_type_from_data(rows, idx)
                columns.append({
                    'name': col_name,
                    'type': type_name
                })
            
            execution_time = (time.time() - start_time) * 1000
            
            return {
                'columns': columns,
                'rows': rows,
                'executionTime': round(execution_time, 2),
                'rowCount': len(rows),
                'sql': sql
            }
        except Exception as e:
            raise e
    
    @staticmethod
    def _infer_type_from_data(rows, col_idx):
        for row in rows[:10]:
            val = row[col_idx]
            if val is not None:
                if isinstance(val, bool):
                    return 'BOOLEAN'
                elif isinstance(val, int):
                    return 'INTEGER'
                elif isinstance(val, float):
                    return 'NUMERIC'
                else:
                    return 'STRING'
        return 'UNKNOWN'
