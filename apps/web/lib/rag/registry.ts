/**
 * Document registry (docs.json)
 */
import fs from "fs/promises";
import path from "path";

const RAG_DATA_DIR = process.env.RAG_DATA_DIR || "data/rag";
const REGISTRY_PATH = path.join(process.cwd(), RAG_DATA_DIR, "docs.json");

export interface DocEntry {
  docId: string;
  filename: string;
  uploadedAt: string;
  chunks: number;
  filePath: string;
}

export async function ensureRegistry(): Promise<void> {
  try {
    await fs.access(REGISTRY_PATH);
  } catch {
    const dir = path.dirname(REGISTRY_PATH);
    await fs.mkdir(dir, { recursive: true });
    await fs.writeFile(REGISTRY_PATH, JSON.stringify([], null, 2));
  }
}

export async function listDocs(): Promise<DocEntry[]> {
  await ensureRegistry();
  const content = await fs.readFile(REGISTRY_PATH, "utf-8");
  return JSON.parse(content);
}

export async function addDoc(entry: DocEntry): Promise<void> {
  const docs = await listDocs();
  docs.push(entry);
  await fs.writeFile(REGISTRY_PATH, JSON.stringify(docs, null, 2));
}

export async function removeDoc(docId: string): Promise<void> {
  const docs = await listDocs();
  const filtered = docs.filter((d) => d.docId !== docId);
  await fs.writeFile(REGISTRY_PATH, JSON.stringify(filtered, null, 2));
}

export async function getDoc(docId: string): Promise<DocEntry | undefined> {
  const docs = await listDocs();
  return docs.find((d) => d.docId === docId);
}

