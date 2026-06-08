from app.services.security_service import SecurityService

class SQLGenerator:
    def __init__(self, query_structure):
        self.query_structure = query_structure
        self.params = {}
        self.param_counter = 0
    
    def _next_param(self, value):
        self.param_counter += 1
        param_name = f'p{self.param_counter}'
        self.params[param_name] = value
        return f':{param_name}'
    
    def _get_table_alias(self, table_id):
        for table in self.query_structure['tables']:
            if table['id'] == table_id:
                return table['alias']
        raise ValueError(f'Table not found: {table_id}')
    
    def _get_table_name(self, table_id):
        for table in self.query_structure['tables']:
            if table['id'] == table_id:
                return table['tableName']
        raise ValueError(f'Table not found: {table_id}')
    
    def _get_qualified_column(self, table_id, column_name):
        alias = self._get_table_alias(table_id)
        col = SecurityService.validate_column_name(column_name)
        return f'{SecurityService.quote_identifier(alias)}.{SecurityService.quote_identifier(col)}'
    
    def generate(self):
        sql_parts = []
        
        select_clause = self._generate_select()
        sql_parts.append(select_clause)
        
        from_clause = self._generate_from()
        sql_parts.append(from_clause)
        
        join_clause = self._generate_joins()
        if join_clause:
            sql_parts.append(join_clause)
        
        where_clause = self._generate_where()
        if where_clause:
            sql_parts.append(where_clause)
        
        group_by_clause = self._generate_group_by()
        if group_by_clause:
            sql_parts.append(group_by_clause)
        
        order_by_clause = self._generate_order_by()
        if order_by_clause:
            sql_parts.append(order_by_clause)
        
        limit = self.query_structure.get('limit', 100)
        sql_parts.append(f'LIMIT {SecurityService.validate_limit(limit)}')
        
        return '\n'.join(sql_parts)
    
    def _generate_select(self):
        selected_fields = self.query_structure.get('selectedFields', [])
        aggregations = self.query_structure.get('aggregations', [])
        
        select_items = []
        
        for field in selected_fields:
            is_aggregated = any(
                agg['tableId'] == field['tableId'] and agg['columnName'] == field['columnName']
                for agg in aggregations
            )
            if is_aggregated:
                continue
            
            col = self._get_qualified_column(field['tableId'], field['columnName'])
            alias = SecurityService.validate_alias(field.get('alias'))
            if alias:
                select_items.append(f'{col} AS {SecurityService.quote_identifier(alias)}')
            else:
                select_items.append(col)
        
        for agg in aggregations:
            func = SecurityService.validate_aggregation(agg['function'])
            col = self._get_qualified_column(agg['tableId'], agg['columnName'])
            alias = SecurityService.validate_alias(agg.get('alias'))
            if alias:
                select_items.append(f'{func}({col}) AS {SecurityService.quote_identifier(alias)}')
            else:
                agg_col_name = agg['columnName']
                select_items.append(f'{func}({col}) AS {SecurityService.quote_identifier(f"{func.lower()}_{agg_col_name}")}')
        
        if not select_items:
            select_items = ['*']
        
        return f'SELECT {", ".join(select_items)}'
    
    def _generate_from(self):
        tables = self.query_structure.get('tables', [])
        if not tables:
            raise ValueError('No tables selected')
        
        first_table = tables[0]
        table_name = SecurityService.validate_table_name(first_table['tableName'])
        alias = SecurityService.validate_identifier(first_table['alias'])
        
        return f'FROM {SecurityService.quote_identifier(table_name)} {SecurityService.quote_identifier(alias)}'
    
    def _generate_joins(self):
        joins = self.query_structure.get('joins', [])
        if not joins:
            return None
        
        join_parts = []
        for join in joins:
            join_type = SecurityService.validate_join_type(join['type'])
            right_table_name = SecurityService.validate_table_name(join['rightTable'])
            right_alias = self._get_table_alias(join.get('rightTableId', ''))
            left_col = self._get_qualified_column(join.get('leftTableId', ''), join['leftColumn'])
            right_col = self._get_qualified_column(join.get('rightTableId', ''), join['rightColumn'])
            
            quoted_right_table = SecurityService.quote_identifier(right_table_name)
            quoted_right_alias = SecurityService.quote_identifier(right_alias)
            if join_type == 'RIGHT' or join_type == 'FULL':
                join_sql = f'LEFT JOIN {quoted_right_table} {quoted_right_alias} ON {left_col} = {right_col}'
            else:
                join_sql = f'{join_type} JOIN {quoted_right_table} {quoted_right_alias} ON {left_col} = {right_col}'
            
            join_parts.append(join_sql)
        
        return '\n'.join(join_parts)
    
    def _generate_where(self):
        where = self.query_structure.get('where')
        if not where:
            return None
        
        condition_sql = self._generate_condition_tree(where)
        if condition_sql:
            return f'WHERE {condition_sql}'
        return None
    
    def _generate_condition_tree(self, node):
        if 'op' in node and 'children' in node:
            op = node['op']
            if op not in ('AND', 'OR'):
                raise ValueError(f'Invalid logical operator: {op}')
            
            children_sql = []
            for child in node['children']:
                child_sql = self._generate_condition_tree(child)
                if child_sql:
                    children_sql.append(child_sql)
            
            if not children_sql:
                return None
            if len(children_sql) == 1:
                return children_sql[0]
            return f'({f" {op} ".join(children_sql)})'
        
        elif 'columnName' in node and 'cmp' in node:
            table_id = node['tableId']
            column_name = node['columnName']
            cmp = SecurityService.validate_operator(node['cmp'])
            value = SecurityService.validate_value(node['value'])
            
            col = self._get_qualified_column(table_id, column_name)
            
            if cmp == 'IN':
                if not isinstance(value, list):
                    raise ValueError('IN operator requires a list value')
                placeholders = [self._next_param(v) for v in value]
                return f'{col} IN ({", ".join(placeholders)})'
            elif cmp == 'LIKE':
                param = self._next_param(value)
                return f'{col} LIKE {param}'
            else:
                param = self._next_param(value)
                return f'{col} {cmp} {param}'
        
        return None
    
    def _generate_group_by(self):
        aggregations = self.query_structure.get('aggregations', [])
        if not aggregations:
            return None
        
        selected_fields = self.query_structure.get('selectedFields', [])
        group_by_fields = []
        
        for field in selected_fields:
            is_aggregated = any(
                agg['tableId'] == field['tableId'] and agg['columnName'] == field['columnName']
                for agg in aggregations
            )
            if not is_aggregated:
                col = self._get_qualified_column(field['tableId'], field['columnName'])
                group_by_fields.append(col)
        
        if group_by_fields:
            return f'GROUP BY {", ".join(group_by_fields)}'
        return None
    
    def _generate_order_by(self):
        return None
    
    def get_params(self):
        return self.params
