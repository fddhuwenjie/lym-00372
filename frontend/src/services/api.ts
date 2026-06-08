import type { TableMetadata, QueryStructure, GeneratedSQL, QueryResult } from '@/types';

const API_BASE = '/api';

export async function getMetadata(): Promise<TableMetadata[]> {
  const response = await fetch(`${API_BASE}/metadata`);
  if (!response.ok) {
    throw new Error('Failed to fetch metadata');
  }
  return response.json();
}

export async function generateSQL(query: QueryStructure): Promise<GeneratedSQL> {
  const response = await fetch(`${API_BASE}/generate-sql`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(query),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to generate SQL');
  }
  return response.json();
}

export async function executeQuery(query: QueryStructure): Promise<QueryResult> {
  const response = await fetch(`${API_BASE}/execute-query`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(query),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to execute query');
  }
  return response.json();
}
