/**
 * Document extraction: PDF, DOCX, HTML, TXT, MD
 */
import mammoth from "mammoth";
// @ts-ignore - html-to-text types
import { convert as htmlToText } from "html-to-text";

// Use dynamic import for pdf-parse (CommonJS module)
const pdfParse = require("pdf-parse");

export async function extractText(buffer: Buffer, filename: string): Promise<string> {
  const ext = filename.split(".").pop()?.toLowerCase();

  try {
    switch (ext) {
      case "pdf":
        const pdfData: any = await pdfParse(buffer);
        return pdfData.text;

      case "docx":
        const docxResult = await mammoth.extractRawText({ buffer });
        return docxResult.value;

      case "html":
      case "htm":
        const htmlText = htmlToText(buffer.toString("utf-8"), {
          wordwrap: false,
          preserveNewlines: true,
        });
        return htmlText;

      case "txt":
      case "md":
      case "markdown":
        return buffer.toString("utf-8");

      default:
        throw new Error(`Unsupported file type: ${ext}`);
    }
  } catch (error) {
    throw new Error(`Extraction failed for ${filename}: ${error instanceof Error ? error.message : String(error)}`);
  }
}

