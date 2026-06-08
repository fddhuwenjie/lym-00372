export interface ColumnMetadata {
  name: string;
  type: string;
  nullable: boolean;
  isPrimaryKey: boolean;
}

export interface ForeignKey {
  constraintName: string;
  fromColumn: string;
  toTable: string;
  toColumn: string;
}

export interface TableMetadata {
  name: string;
  columns: ColumnMetadata[];
  foreignKeys: ForeignKey[];
}

export interface TableNode {
  id: string;
  tableName: string;
  alias: string;
  position: { x: number; y: number };
}

export type JoinType = 'INNER' | 'LEFT' | 'RIGHT' | 'FULL';

export interface Join {
  id: string;
  type: JoinType;
  leftTableId: string;
  leftColumn: string;
  rightTableId: string;
  rightColumn: string;
  leftTable: string;
  rightTable: string;
}

export interface SelectedField {
  tableId: string;
  columnName: string;
  alias?: string;
}

export type ComparisonOperator = '=' | '!=' | '>' | '<' | '>=' | '<=' | 'LIKE' | 'IN';

export interface WhereClause {
  tableId: string;
  columnName: string;
  cmp: ComparisonOperator;
  value: string | number | boolean | (string | number)[];
  id: string;
}

export interface WhereCondition {
  op: 'AND' | 'OR';
  children: (WhereCondition | WhereClause)[];
  id: string;
}

export type AggregationFunction = 'SUM' | 'AVG' | 'COUNT' | 'MAX' | 'MIN';

export interface Aggregation {
  tableId: string;
  columnName: string;
  function: AggregationFunction;
  alias?: string;
}

export interface QueryStructure {
  tables: TableNode[];
  joins: Join[];
  selectedFields: SelectedField[];
  where: WhereCondition | null;
  aggregations: Aggregation[];
  limit: number;
}

export interface GeneratedSQL {
  sql: string;
  params: Record<string, any>;
}

export interface ResultColumn {
  name: string;
  type: string;
}

export interface QueryResult {
  columns: ResultColumn[];
  rows: any[][];
  executionTime: number;
  rowCount: number;
  sql?: string;
}

export type WhereNode = WhereCondition | WhereClause;

export function isWhereCondition(node: WhereNode): node is WhereCondition {
  return 'op' in node && 'children' in node;
}

export function isWhereClause(node: WhereNode): node is WhereClause {
  return 'columnName' in node && 'cmp' in node;
}
