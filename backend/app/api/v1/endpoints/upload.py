from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from app.auth.deps import get_current_user
from app.models.user import User
from app.rag.embeddings import get_embedding_service
from app.rag.vector_store import vector_store
from app.rag.bm25_store import bm25_store, simple_tokenize
import os
import tempfile
from PyPDF2 import PdfReader
from langsmith import traceable

router = APIRouter()

def extract_text_from_file(file_path: str, filename: str) -> str:
    if filename.lower().endswith('.txt'):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="File encoding not supported. Use UTF-8 encoded text files.")
    elif filename.lower().endswith('.pdf'):
        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error reading PDF: {str(e)}")
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type. Use TXT or PDF.")

@router.post("/upload")
@traceable(name="File Upload Processing")
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    print(f"Upload attempt by user {current_user.id}: {file.filename}")
    if not file.filename.lower().endswith(('.txt', '.pdf')):
        print(f"Invalid file type: {file.filename}")
        raise HTTPException(status_code=400, detail="Unsupported file type. Use TXT or PDF.")

    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_path = temp_file.name
    print(f"File saved to temp: {temp_path}")

    try:
        # Extract text
        text = extract_text_from_file(temp_path, file.filename)
        print(f"Extracted text length: {len(text)}")
        if not text.strip():
            raise HTTPException(status_code=400, detail="No text found in file.")

        # Prepare for embedding
        embedding_service = get_embedding_service()
        embedding = embedding_service.encode([text])[0]
        print("Embedding generated")

        # Metadata
        meta = {
            "filename": file.filename,
            "user_id": current_user.id,
            "content": text[:500]  # Truncate for metadata
        }

        # Add to vector store
        vector_store.add_documents([embedding], [meta])
        print("Added to vector store")

        # Add to BM25
        tokens = simple_tokenize(text)
        bm25_store.corpus_tokens.append(tokens)
        bm25_store.metadata.append(meta)
        bm25_store.bm25 = None  # Reset to rebuild on next search
        print("Added to BM25 store")

        # Save stores (optional, since in memory for now)
        vector_store.save()
        bm25_store.save()
        print("Stores saved")

        return {"message": f"File '{file.filename}' uploaded and processed successfully."}

    except Exception as e:
        print(f"Error processing file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    finally:
        # Clean up temp file
        os.unlink(temp_path)