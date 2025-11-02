#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LLM客户端模块
用于与大语言模型交互，处理文档内容并提取结构化知识图谱数据
"""

import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain_community.callbacks.manager import get_openai_callback
from model.Structure_model import BearingFaultKnowledgeGraph, parser

# 加载.env文件中的环境变量
load_dotenv()


class LLMClient:
    """LLM客户端类"""
    
    def __init__(self, model_name: str = "", temperature: float = 0.4, base_url: str = ""):
        """
        初始化LLM客户端
        
        Args:
            model_name: 使用的模型名称
            temperature: 生成文本的随机性参数
            base_url: API的基础URL
        """
        # 从环境变量获取配置参数
        api_key = os.getenv("API_KEY")
        base_url = base_url or os.getenv("BASE_URL")
        model_name = model_name or os.getenv("MODEL_NAME") or model_name
        
        if not api_key:
            raise ValueError("请在.env文件中设置API_KEY环境变量")
        
        # 配置ChatOpenAI客户端
        model_kwargs = {
            "temperature": temperature,
            "openai_api_key": api_key
        }
        
        if base_url:
            model_kwargs["openai_api_base"] = base_url
            
        if model_name:
            model_kwargs["model_name"] = model_name
        
        self.model = ChatOpenAI(**model_kwargs)
    
    def extract_knowledge_graph(self, prompt: str) -> BearingFaultKnowledgeGraph:
        """
        通过LLM从提示词中提取知识图谱数据
        
        Args:
            prompt: 发送给LLM的提示词
            
        Returns:
            结构化的知识图谱数据
        """
        try:
            # 构建消息
            messages = [
                SystemMessage(content="你是一个专业的知识图谱构建助手。"),
                HumanMessage(content=prompt)
            ]
            
            # 调用LLM并获取响应
            with get_openai_callback() as cb:
                response = self.model.invoke(messages)
                print(f"LLM调用成本: {cb.total_cost} USD")
            
            # 解析响应为结构化数据
            kg_data = parser.parse(response.content)
            return kg_data
            
        except Exception as e:
            raise Exception(f"LLM处理失败: {str(e)}")
    
    def process_text_chunk(self, text_chunk: str, context_info: Optional[str] = None) -> BearingFaultKnowledgeGraph:
        """
        处理单个文本块，提取知识图谱数据
        
        Args:
            text_chunk: 文本块内容
            context_info: 上下文信息（可选）
            
        Returns:
            结构化的知识图谱数据
        """
        from Structure_model import format_instructions
        
        # 构建提示词
        prompt = f"""你是一个专业的知识图谱构建助手。你的任务是从技术文档中提取结构化的轴承故障相关信息，
并将它们组织成知识图谱的形式。

请仔细阅读以下文档片段，并提取其中的轴承故障相关信息。你需要识别：
1. 轴承故障类型及其属性（名称、严重程度等）
2. 故障原因及其影响
3. 故障在信号中的表现形式
4. 特征频率信息
5. 诊断方法
6. 影响因素

请严格按照以下JSON格式输出，不要添加任何额外的文字说明：

{format_instructions}

文档内容：
{text_chunk}

"""
        
        # 如果有上下文信息，则添加上下文提示
        if context_info:
            prompt += f"""
重要上下文信息（请参考但不要重复提取）：
{context_info}

请基于以上上下文信息和当前文档内容，提取新增的或不同的信息。
"""
        
        # 调用LLM提取知识图谱
        return self.extract_knowledge_graph(prompt)


# 使用示例
if __name__ == "__main__":
    # 使用示例（需要设置OPENAI_API_KEY环境变量）
    # client = LLMClient()
    # result = client.process_text_chunk("轴承在运行过程中出现过热现象，这通常是由于润滑不良导致的。")
    # print(result)
    pass