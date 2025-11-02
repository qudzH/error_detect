from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from typing import List
import os
import tempfile
import shutil
from server.document_processor import DocumentProcessor

router = APIRouter()

# 初始化文档处理器
processor = DocumentProcessor()

@router.get("/process", response_class=HTMLResponse)
async def read_root():
    """返回前端页面"""
    frontend_path = os.path.join(os.path.dirname(__file__), "frontend.html")
    if os.path.exists(frontend_path):
        with open(frontend_path, "r", encoding="utf-8") as file:
            html_content = file.read()
        return HTMLResponse(content=html_content, status_code=200)
    else:
        return HTMLResponse(content="<h1>Frontend page not found</h1>", status_code=404)

@router.post("/process-document/")
async def process_document(file: UploadFile = File(...)):
    """
    处理上传的文档文件
    
    Args:
        file: 上传的文档文件
        
    Returns:
        处理结果，包括文本内容和知识图谱数据
    """
    # 支持的文件类型
    supported_extensions = [".md", ".txt", ".docx"]
    
    # 检查文件扩展名
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in supported_extensions:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: {file_extension}。支持的格式: {supported_extensions}")
    
    # 创建临时文件
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            tmp_file_path = tmp_file.name
        
        # 处理文档
        result = processor.process_document(tmp_file_path)
        
        # 清理临时文件
        os.unlink(tmp_file_path)
        
        # 返回结果
        return {
            "filename": file.filename,
            "text_content": result["text_content"],
            "chunks": result["chunks"],
            "knowledge_graph": result["knowledge_graph"]  # 注意：这里可能需要序列化处理
        }
    except Exception as e:
        # 确保临时文件被清理
        if 'tmp_file_path' in locals():
            os.unlink(tmp_file_path)
        raise HTTPException(status_code=500, detail=f"处理文档时出错: {str(e)}")

@router.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(router, host="0.0.0.0", port=8000)