#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
启动FastAPI服务器的脚本
"""

import uvicorn
import sys
import os

# 将项目根目录添加到Python路径中
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    # 导入并运行FastAPI应用
    from main import app
    
    print("正在启动轴承故障诊断文档处理系统...")
    print("访问 http://localhost:8000 查看应用")
    print("按 Ctrl+C 停止服务器")
    
    # 启动服务器
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # 开发模式下启用热重载
        workers=1     # 工作进程数
    )