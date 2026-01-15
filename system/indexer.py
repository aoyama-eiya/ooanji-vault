# Fix C++ locale issue before any C++ library loads
import os
os.environ['LC_ALL'] = 'POSIX'
os.environ['LANG'] = 'POSIX'

import sys
import json
import sqlite3
import logging
import time
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
import gc
import hashlib

# Llama.cpp
try:
    from llama_cpp import Llama
except ImportError:
    Llama = None

# ChromaDB
try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    chromadb = None

# Document Loaders
try:
    import docx
except ImportError:
    docx = None
try:
    import openpyxl
except ImportError:
    openpyxl = None

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/indexing.log", mode='w'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("indexer")

# --- Configuration ---
BASE_DIR = Path(__file__).parent.absolute()
MODELS_DIR = BASE_DIR / "models"
MNT_DIR = BASE_DIR / "mnt"
INTERNAL_NAS_DIR = BASE_DIR / "internal_storage"
CHROMA_DB_DIR = BASE_DIR / "chroma_db"
DB_PATH = BASE_DIR / "users.db"

# Ensure directories exist
MODELS_DIR.mkdir(exist_ok=True)
MNT_DIR.mkdir(exist_ok=True)
INTERNAL_NAS_DIR.mkdir(exist_ok=True)

class ModelManager:
    def __init__(self):
        self.current_embed_model = None
        self.current_embed_path = None

    def get_embed_model(self, model_path: Path):
        if self.current_embed_model and self.current_embed_path == model_path:
            return self.current_embed_model

        # Unload previous model
        if self.current_embed_model:
            del self.current_embed_model
            self.current_embed_model = None
            gc.collect()

        logger.info(f"Loading Embedding Model: {model_path}")

        try:
            self.current_embed_model = Llama(
                model_path=str(model_path),
                embedding=True,      # Set to embedding mode
                n_gpu_layers=0,      # Force CPU for stability
                n_ctx=2048,
                verbose=False
            )
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise e
        self.current_embed_path = model_path
        return self.current_embed_model

    def get_chat_model(self):
        # Path to Qwen 2.5 1.5B (Fast and capable for summaries)
        chat_model_path = MODELS_DIR / "qwen2-1.5b-instruct-q8_0.gguf"
        
        if self.current_embed_model and str(self.current_embed_path) != str(chat_model_path):
             logger.info("Unloading embedding model to load chat model...")
             del self.current_embed_model
             self.current_embed_model = None
             self.current_embed_path = None
             gc.collect()

        if self.current_embed_model and str(self.current_embed_path) == str(chat_model_path):
            return self.current_embed_model

        if not chat_model_path.exists():
            # Fallback to any gguf if specific one not found (excluding embeds)
            candidates = list(MODELS_DIR.glob("*.gguf"))
            candidates = [p for p in candidates if "embed" not in p.name.lower()]
            if not candidates:
                logger.error("No chat model found for summarization.")
                return None
            chat_model_path = candidates[0]

        logger.info(f"Loading Summarization Model: {chat_model_path}")
        try:
            self.current_embed_model = Llama(
                model_path=str(chat_model_path),
                n_gpu_layers=0,
                n_ctx=2048, # Increased context for safety
                verbose=False,
                use_mmap=False
            )
            self.current_embed_path = chat_model_path
            return self.current_embed_model
        except Exception as e:
            logger.error(f"Failed to load chat model: {e}")
            return None

model_manager = ModelManager()

def generate_summary(text: str) -> str:
    if not text: return ""
    llm = model_manager.get_chat_model()
    if not llm: return "Summary generation unavailable."

    try:
        # Use first 800 chars for summary to keep it safe within context
        preview = text[:800]
        messages = [
            {"role": "system", "content": "You are a helpful assistant. Summarize the provided document text in 3 concise Japanese sentences."},
            {"role": "user", "content": f"Document Snippet:\n{preview}\n\nSummary:"}
        ]
        
        response = llm.create_chat_completion(messages=messages, max_tokens=200, temperature=0.3)
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        logger.error(f"Summarization error: {e}")
        return "Summary generation failed."

class GGUFEmbeddingFunction:
    def __init__(self, model_path: Path):
        self.model_path = model_path
        
    def __call__(self, input: List[str]) -> List[List[float]]:
        try:
            llm = model_manager.get_embed_model(self.model_path)
            if not llm:
                logger.error("Embedding model not loaded")
                return [[] for _ in input] # Return empty if failed
                
            embeddings = []
            for i, text in enumerate(input):
                try:
                    # Llama.cpp embedding
                    embed = llm.create_embedding(text)
                    embeddings.append(embed['data'][0]['embedding'])
                except Exception as e:
                    logger.error(f"Failed to create embedding for text {i}: {e}")
                    # Return zero vector as fallback
                    embeddings.append([0.0] * 768)  # nomic-embed has 768 dimensions
            return embeddings
        except Exception as e:
            logger.error(f"Critical error in embedding function: {e}")
            return [[0.0] * 768 for _ in input]

def read_docx_file(path: Path) -> str:
    if not docx: return ""
    try:
        doc = docx.Document(path)
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        logger.warning(f"Error reading docx {path}: {e}")
        return ""

def read_excel_file(path: Path) -> str:
    if not openpyxl: return ""
    try:
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        text = []
        for sheet in wb.worksheets:
            text.append(f"--- Sheet: {sheet.title} ---")
            for row in sheet.iter_rows(values_only=True):
                row_text = [str(cell) for cell in row if cell is not None]
                if row_text:
                    text.append(" ".join(row_text))
        return "\n".join(text)
    except Exception as e:
        logger.warning(f"Error reading xlsx {path}: {e}")
        return ""

def recursive_character_text_splitter(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    chunks = []
    if not text:
        return chunks
    
    start = 0
    text_len = len(text)
    
    while start < text_len:
        end = start + chunk_size
        if end >= text_len:
            chunks.append(text[start:])
            break
        
        # Try to find a split point (newline or space)
        split_point = -1
        # Look for newline in the overlap area
        search_start = max(start, end - chunk_overlap)
        
        # Prioritize newlines
        for i in range(end, search_start, -1):
            if text[i] == '\n':
                split_point = i
                break
        
        if split_point == -1:
            # Look for space
            for i in range(end, search_start, -1):
                if text[i] == ' ':
                    split_point = i
                    break
        
        if split_point != -1:
            chunks.append(text[start:split_point])
            start = split_point + 1 # Skip the delimiter
        else:
            # Hard split
            chunks.append(text[start:end])
            start = end - chunk_overlap
            
    return chunks



# Global log buffer
log_buffer = []

def add_log(message: str):
    global log_buffer
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    print(log_entry) # Stdout for docker logs
    log_buffer.append(log_entry)
    if len(log_buffer) > 50:
        log_buffer.pop(0)

def update_status(status: str, progress: float, is_indexing: bool, processed: int, total: int):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Ensure table exists (indexer needs to be robust)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        status_data = {
            "status": status,
            "progress": progress,
            "is_indexing": is_indexing,
            "processed_files": processed,
            "total_files": total,
            "last_updated": datetime.now().isoformat(),
            "indexing_log": log_buffer
        }
        
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", 
                      ("indexing_status", json.dumps(status_data)))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Failed to update status: {e}")

def check_stop_flag() -> bool:
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = 'stop_indexing_flag'")
        row = cursor.fetchone()
        conn.close()
        if row and row[0] == 'true':
            return True
        return False
    except:
        return False

def main():
    logger.info("Starting indexing process...")
    global log_buffer
    log_buffer = []
    
    # Initialize status
    add_log("Starting indexing process...")
    update_status("Starting...", 0, True, 0, 0)
    
    # Reset stop flag
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", ("stop_indexing_flag", "false"))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Failed to reset stop flag: {e}")

    try:
        # Handle storage mode from command line
        storage_mode = "nas"
        if len(sys.argv) > 1:
            storage_mode = sys.argv[1]
            
        if storage_mode == "internal":
            source_dir = INTERNAL_NAS_DIR
        else:
            source_dir = MNT_DIR
        
        add_log(f"Starting indexing in '{storage_mode}' mode...")
        add_log(f"Scanning directory: {source_dir}")
        if not any(source_dir.iterdir()):
             add_log(f"WARNING: Directory {source_dir} appears empty.")
        
        if not source_dir.exists():
            logger.error(f"Source directory not found: {source_dir}")
            update_status(f"Error: Directory not found", 0, False, 0, 0)
            return

        # Initialize ChromaDB
        logger.info("Initializing ChromaDB...")
        client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))
        
        # Embedding Model
        embed_model_path = MODELS_DIR / "nomic-embed-text-v1.5.f16.gguf"
        if not embed_model_path.exists():
            logger.error(f"Embedding model not found: {embed_model_path}")
            update_status("Error: Embedding model missing", 0, False, 0, 0)
            return
            
        embedding_function = GGUFEmbeddingFunction(model_path=embed_model_path)
        
        # Separate collections for NAS and Internal storage
        collection_name = f"documents_{storage_mode}"
        logger.info(f"Using ChromaDB collection: {collection_name}")
        
        collection = client.get_or_create_collection(
            name=collection_name,
            embedding_function=embedding_function
        )
        logger.info("ChromaDB collection loaded.")

        # DB for file state (Updated Schema)
        db_conn = sqlite3.connect(DB_PATH)
        db_cursor = db_conn.cursor()
        
        # Check if table exists and has 'summary' column
        db_cursor.execute("PRAGMA table_info(file_index_state)")
        columns = [info[1] for info in db_cursor.fetchall()]
        
        if 'file_index_state' not in columns and not columns: # Table doesn't exist
            db_cursor.execute('''
                CREATE TABLE IF NOT EXISTS file_index_state (
                    path TEXT PRIMARY KEY,
                    modified_time REAL,
                    last_seen REAL,
                    summary TEXT
                )
            ''')
        elif 'summary' not in columns: # Table exists but needs upgrade
            try:
                db_cursor.execute("ALTER TABLE file_index_state ADD COLUMN summary TEXT")
            except Exception as e:
                logger.warning(f"Could not add summary column (might exist): {e}")
        
        db_conn.commit()

        # Scan
        logger.info("Starting scan...")
        update_status("Scanning files...", 0, True, 0, 0)
        
        scan_start_time = time.time()
        batch_size = 10
        current_batch_ids, current_batch_docs, current_batch_metadatas, current_batch_embeddings = [], [], [], []
        scanned_count, processed_count = 0, 0
        
        # Count total files first for progress (optional, but good for UX)
        # For now, we'll just increment scanned_count
        
        for root, _, files in os.walk(source_dir):
            if check_stop_flag():
                logger.info("Stop flag detected. Halting scan.")
                break
                
            for file in files:
                if check_stop_flag(): break
                
                scanned_count += 1
                file_path = Path(root) / file
                file_key = str(file_path)
                
                if scanned_count % 5 == 0:
                    update_status(f"Scanning: {file}", 0, True, processed_count, scanned_count)

                if not file.endswith(('.txt', '.md', '.json', '.py', '.js', '.ts', '.html', '.css', '.csv', '.docx', '.xlsx')):
                    continue
                
                # logger.info(f"[{scanned_count}] Checking: {file_key}")
                    
                try:
                    stat = file_path.stat()
                    mod_time = stat.st_mtime

                    if stat.st_size > 1024 * 1024 * 1024: # 1GB limit
                        continue

                    db_cursor.execute("SELECT modified_time FROM file_index_state WHERE path = ?", (file_key,))
                    result = db_cursor.fetchone()
                    
                    if result and result[0] == mod_time:
                        db_cursor.execute("UPDATE file_index_state SET last_seen = ? WHERE path = ?", (scan_start_time, file_key))
                        continue
                        
                    add_log(f"Processing: {file}")
                    update_status(f"Processing: {file}", 0, True, processed_count, scanned_count)
                    
                    content = ""
                    if file_path.suffix == '.docx':
                        content = read_docx_file(file_path)
                    elif file_path.suffix == '.xlsx':
                        content = read_excel_file(file_path)
                    else:
                        if stat.st_size > 10 * 1024 * 1024:
                            logger.info(f"    - Skipping text read >10MB for: {file}")
                            continue
                        try:
                            content = file_path.read_text(encoding='utf-8', errors='ignore')
                        except Exception as read_err:
                            logger.warning(f"    - Read error: {read_err}")
                            continue

                    if not content or not content.strip():
                        db_cursor.execute("INSERT OR REPLACE INTO file_index_state (path, modified_time, last_seen, summary) VALUES (?, ?, ?, ?)",
                                          (file_key, mod_time, scan_start_time, ""))
                        continue

                    # --- 4-Layer Architecture: Generate Summary Layer ---
                    summary = ""
                    try:
                        # logger.info(f"    - Generating summary...")
                        summary = generate_summary(content)
                        # logger.info(f"    - Summary generated.")
                    except Exception as sum_err:
                        add_log(f"Warning: Summary failed for {file}: {sum_err}")
                    
                    # Store State & Summary immediately
                    db_cursor.execute("INSERT OR REPLACE INTO file_index_state (path, modified_time, last_seen, summary) VALUES (?, ?, ?, ?)",
                                      (file_key, mod_time, scan_start_time, summary))
                    db_conn.commit()

                    chunks = recursive_character_text_splitter(content, chunk_size=1000, chunk_overlap=200)
                    file_hash = hashlib.md5(file_key.encode()).hexdigest()
                    mod_time_iso = datetime.fromtimestamp(mod_time).isoformat()

                    collection.delete(where={"path": file_key})

                    for j, chunk in enumerate(chunks):
                        raw_chunk = chunk
                        # nomic-embed likes search_document: prefix for documents
                        prefixed_chunk = f"search_document: {raw_chunk}"
                        chunk_id = f"{file_hash}_{j}"
                        
                        current_batch_ids.append(chunk_id)
                        current_batch_docs.append(raw_chunk)
                        current_batch_metadatas.append({"filename": file_path.name, "path": file_key, "modified_at": mod_time_iso, "chunk_index": j, "total_chunks": len(chunks)})
                        
                        # Calculate embedding with prefix
                        embeds = embedding_function([prefixed_chunk])
                        current_batch_embeddings.append(embeds[0])
                        
                        if len(current_batch_ids) >= batch_size:
                            try:
                                collection.add(
                                    ids=current_batch_ids, 
                                    documents=current_batch_docs, 
                                    metadatas=current_batch_metadatas,
                                    embeddings=current_batch_embeddings
                                )
                            except Exception as add_err:
                                add_log(f"Error adding batch to Chroma: {add_err}")
                            current_batch_ids, current_batch_docs, current_batch_metadatas, current_batch_embeddings = [], [], [], []

                    # Update state (redundant but safe)
                    db_cursor.execute("UPDATE file_index_state SET last_seen = ? WHERE path = ?",
                                      (scan_start_time, file_key))
                    db_conn.commit()
                    
                    processed_count += 1
                    add_log(f"Indexed: {file} ({len(chunks)} chunks)")
                    update_status(f"Indexed: {file}", 0, True, processed_count, scanned_count)

                except Exception as e:
                    add_log(f"Error processing {file}: {e}")

        # Final Batch
        if current_batch_ids and not check_stop_flag():
            logger.info(f"Adding final batch of {len(current_batch_ids)} chunks...")
            try:
                collection.add(
                    ids=current_batch_ids, 
                    documents=current_batch_docs, 
                    metadatas=current_batch_metadatas,
                    embeddings=current_batch_embeddings
                )
                db_conn.commit()
            except Exception as e:
                logger.error(f"ERROR adding final batch: {e}")

        # Cleanup old files
        if not check_stop_flag():
            logger.info("Cleaning up deleted files from index...")
            db_cursor.execute("SELECT path FROM file_index_state WHERE last_seen < ?", (scan_start_time,))
            deleted_files = db_cursor.fetchall()
            for (path,) in deleted_files:
                logger.info(f"Removing deleted file from index: {path}")
                collection.delete(where={"path": path})
                db_cursor.execute("DELETE FROM file_index_state WHERE path = ?", (path,))
            db_conn.commit()

        db_conn.close()
        db_conn = sqlite3.connect(DB_PATH)
        db_cursor = db_conn.cursor()
        db_cursor.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', ('last_indexed_at', datetime.now().isoformat()))
        db_conn.commit()
        db_conn.close()
        
        logger.info("Indexing completed.")
        update_status("Completed", 100, False, processed_count, scanned_count)

    except Exception as e:
        logger.error(f"Global Indexing Error: {e}")
        update_status(f"Failed: {str(e)}", 0, False, 0, 0)

if __name__ == "__main__":
    main()
