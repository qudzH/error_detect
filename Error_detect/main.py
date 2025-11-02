from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn
import os

from router.process_router import router as process_router

app = FastAPI()

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含路由，使用空字符串作为前缀，并将process_router的prefix设置为""
app.include_router(process_router, prefix="")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    # 创建导航页面
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>轴承故障诊断系统导航</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
                background-color: #f5f5f5;
            }
            .container {
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background-color: white;
                border-radius: 10px;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
            }
            h1 {
                text-align: center;
                color: #333;
            }
            .nav-links {
                display: flex;
                flex-direction: column;
                gap: 20px;
                margin-top: 30px;
            }
            .nav-link {
                padding: 20px;
                background-color: #007bff;
                color: white;
                text-align: center;
                text-decoration: none;
                border-radius: 5px;
                font-size: 18px;
                transition: background-color 0.3s;
            }
            .nav-link:hover {
                background-color: #0056b3;
            }
            .description {
                margin-top: 30px;
                padding: 15px;
                background-color: #e9ecef;
                border-radius: 5px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>轴承故障诊断系统</h1>
            <div class="nav-links">
                <a href="/process" class="nav-link">文档处理系统</a>
            </div>
            <div class="description">
                <h2>系统说明</h2>
                <p>欢迎使用轴承故障诊断系统。请点击上方链接进入文档处理系统，您可以上传轴承故障相关的文档（支持 .md, .txt, .docx 格式），系统将自动分析文档内容并提取结构化的故障知识图谱。</p>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)