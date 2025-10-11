/**
 * LanceDB vector store
 */
import { connect } from "@lancedb/lancedb";
import path from "path";

const RAG_DATA_DIR = process.env.RAG_DATA_DIR || "data/rag";
const DB_PATH = path.join(process.cwd(), RAG_DATA_DIR, "lancedb");
const TABLE_NAME = "documents";

export interface VectorRow {
  docId: string;
  chunkIndex: number;
  text: string;
  vector: number[];
  filename: string;
}

export interface SearchResult {
  docId: string;
  chunkIndex: number;
  text: string;
  score: number;
  filename: string;
}

let dbInstance: any = null;

async function getDb(): Promise<any> {
  if (!dbInstance) {
    dbInstance = await connect(DB_PATH);
  }
  return dbInstance;
}

export async function ensureTable(): Promise<any> {
  const db = await getDb();
  const tableNames = await db.tableNames();

  if (tableNames.includes(TABLE_NAME)) {
    return await db.openTable(TABLE_NAME);
  }

  // Create table with first row (LanceDB will infer schema)
  const sampleRow: VectorRow = {
    docId: "init",
    chunkIndex: 0,
    text: "initialization",
    vector: new Array(3072).fill(0),
    filename: "init.txt",
  };

  const table = await db.createTable(TABLE_NAME, [sampleRow]);
  
  // Delete the sample row
  await table.delete(`docId = 'init'`);
  
  return table;
}

export async function addVectors(rows: VectorRow[]): Promise<void> {
  const table = await ensureTable();
  await table.add(rows);
}

export async function search(queryVector: number[], topK: number = 6): Promise<SearchResult[]> {
  const table = await ensureTable();
  
  const results = await table
    .search(queryVector)
    .limit(topK)
    .toArray();

  return results.map((row: any) => ({
    docId: row.docId,
    chunkIndex: row.chunkIndex,
    text: row.text,
    score: row._distance || 0,
    filename: row.filename,
  }));
}

export async function deleteByDocId(docId: string): Promise<void> {
  const table = await ensureTable();
  await table.delete(`docId = '${docId}'`);
}

