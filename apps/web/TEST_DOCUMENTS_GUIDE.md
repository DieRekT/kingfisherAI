# Test Documents for RAG System

## Quick Start - Upload Existing Project Docs

The project already has great documentation files you can use to test the RAG system:

### 1. From Project Root
- `README.md` - Main project documentation
- `DEVELOPER_GUIDE.md` - Developer setup and guidelines

### 2. From apps/web/
- `AI_SDK_V5_INTEGRATION.md` - AI SDK v5 integration guide
- `RAG_ADDON_INSTALL.md` - RAG system documentation

## How to Test

### Step 1: Start the Dev Server
```bash
cd apps/web
npm run dev
```

### Step 2: Open the RAG Dropzone
Visit: http://localhost:3000/labs/dropzone

### Step 3: Upload Documents
1. Click the upload area or drag files
2. Upload the markdown files mentioned above
3. Wait for processing (typically 2-5 seconds per document)

### Step 4: Test Search
Example queries to try:
- "How do I set up the RAG system?"
- "What are the AI SDK v5 features?"
- "Tell me about the developer setup"

### Step 5: Test Chat
Ask questions like:
- "Summarize the RAG addon features"
- "What dependencies are needed for AI SDK v5?"
- "How do I configure chunk sizes?"

## Creating Additional Test Documents

### Option 1: Convert Project Docs to PDF
```bash
# If you have pandoc installed:
cd /home/lucifer/Projects/kingfisherAI
pandoc README.md -o test-readme.pdf
pandoc DEVELOPER_GUIDE.md -o test-devguide.pdf
```

### Option 2: Create Sample Text Files
Create simple `.txt` files with test content:

```bash
cd /home/lucifer/Projects/kingfisherAI
cat > test-sample.txt << 'EOF'
# Sample Document for RAG Testing

## About the System
This is a test document for the RAG (Retrieval-Augmented Generation) system.

## Features
- Semantic search capabilities
- AI-powered Q&A with citations
- Support for multiple file formats (PDF, DOCX, HTML, TXT, MD)

## Configuration
The system uses chunking to break documents into smaller pieces for better retrieval.
Default chunk size is 900 tokens with 100 token overlap.

## Testing Tips
1. Upload documents with varied content
2. Try different query types
3. Check citation accuracy
4. Adjust chunk sizes in configuration
EOF
```

### Option 3: Download Sample PDFs
You can download sample PDFs from:
- https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf
- Or use any technical documentation PDF you have

## File Format Support

The RAG system supports:
- **PDF** (.pdf) - Best for formatted documents
- **Word** (.docx) - Microsoft Word documents
- **HTML** (.html, .htm) - Web pages
- **Text** (.txt) - Plain text files
- **Markdown** (.md) - Documentation files

## Expected Results

### After Upload
- Document appears in "Documents" list
- Shows chunk count (varies by document size)
- Timestamp of upload

### After Search
- Returns top-K relevant chunks (default: 6)
- Shows similarity scores
- Displays source file and chunk location

### After Chat
- Streams AI-generated answer
- Includes inline citations [S1], [S2], etc.
- Lists sources with filenames and chunk indices

## Troubleshooting

### "No API Key" Error
Make sure you've created `.env.local` with your OpenAI API key:
```bash
cd apps/web
cp .env.example .env.local
# Edit .env.local and add your OpenAI API key
```

### Large File Upload Fails
- Next.js has default ~4MB limit for route handlers
- Try splitting large documents
- Or increase limit in next.config.js

### Search Returns No Results
- Make sure documents are uploaded successfully
- Check that OpenAI API key is valid
- Try different query phrasing

## Configuration Testing

Use the RAG Configuration panel to test different settings:

### Chunk Size
- **300-600 tokens**: More precise, granular results
- **900 tokens** (default): Balanced
- **1200-1500 tokens**: More context, broader answers

### Top K
- **1-3**: Fast, focused results
- **6** (default): Good balance
- **10-20**: More comprehensive, slower

### Embedding Model
- **text-embedding-3-large**: Best quality (3072 dims)
- **text-embedding-3-small**: Faster, cheaper (1536 dims)

**Note**: Changing embedding model requires re-uploading all documents.

## Next Steps

After successful testing:
1. Try with your own domain-specific documents
2. Experiment with different chunk sizes
3. Test edge cases (very long queries, special characters, etc.)
4. Monitor OpenAI API usage in your dashboard

---

**Created**: 2025-10-11  
**Location**: `/apps/web/TEST_DOCUMENTS_GUIDE.md`

