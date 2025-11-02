#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
文档处理模块
用于接收MD、Word等文件，解析文本内容，并通过LLM提取结构化知识图谱数据
"""

import os
import tempfile
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
from pydantic import BaseModel
# 从现有模块导入知识图谱模型
from model.Structure_model import BearingFaultKnowledgeGraph, parser, format_instructions


class DocumentProcessor:
    """文档处理器主类"""
    
    def __init__(self, max_context_length: int = 3000):
        self.parsers = {
            '.md': MarkdownParser(),
            '.txt': TextParser(),
            '.docx': WordParser(),
        }
        self.max_context_length = max_context_length  # LLM最大上下文长度限制
    
    def add_parser(self, extension: str, parser: 'DocumentParser'):
        """添加新的文档解析器"""
        self.parsers[extension] = parser
    
    def process_document(self, file_path: str) -> Dict[str, Any]:
        """
        处理文档的主入口函数
        
        Args:
            file_path: 文档文件路径
            
        Returns:
            包含解析结果和知识图谱数据的字典
        """
        # 检查文件是否存在
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 1. 获取文件扩展名
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()  # 转换为小写以确保匹配
        
        # 2. 选择合适的解析器
        if ext not in self.parsers:
            raise ValueError(f"不支持的文件格式: {ext}。支持的格式: {list(self.parsers.keys())}")
        
        parser = self.parsers[ext]
        
        try:
            # 3. 解析文档内容
            text_content = parser.parse(file_path)
            
            # 4. 如果文本过长，进行分块处理
            chunks = self._chunk_text(text_content)
            
            # 5. 通过LLM提取知识图谱数据
            kg_data = self._extract_knowledge_graph(chunks)
            
            return {
                "original_file": file_path,
                "text_content": text_content,
                "chunks": chunks,
                "knowledge_graph": kg_data
            }
        except Exception as e:
            raise Exception(f"处理文档时出错: {str(e)}")
    
    def _chunk_text(self, text: str) -> List[str]:
        """
        将长文本分块，确保每块不超过最大上下文长度，同时尽量保持语义完整性
        
        Args:
            text: 原始文本内容
            
        Returns:
            分块后的文本列表
        """
        if len(text) <= self.max_context_length:
            return [text]
        
        # 按段落和句子进行分割
        paragraphs = text.split('\n\n')  # 先按段落分割
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            # 如果段落本身就很短，尝试合并
            if len(paragraph) < 100:
                if len(current_chunk) + len(paragraph) <= self.max_context_length:
                    current_chunk += "\n\n" + paragraph
                    continue
                else:
                    # 保存当前块并开始新块
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = paragraph
                    continue
            
            # 如果段落太大，需要进一步分割
            if len(paragraph) > self.max_context_length:
                # 按句子分割
                sentences = self._split_sentences(paragraph)
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) <= self.max_context_length:
                        current_chunk += " " + sentence
                    else:
                        # 保存当前块并开始新块
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        current_chunk = sentence
            else:
                # 段落大小适中
                if len(current_chunk) + len(paragraph) <= self.max_context_length:
                    current_chunk += "\n\n" + paragraph
                else:
                    # 保存当前块并开始新块
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = paragraph
        
        # 添加最后一个块
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        return chunks
    
    def _split_sentences(self, text: str) -> List[str]:
        """
        智能分割句子，考虑多种句子结束符
        
        Args:
            text: 需要分割的文本
            
        Returns:
            句子列表
        """
        import re
        # 使用正则表达式分割句子，考虑句号、感叹号、问号等
        sentences = re.split(r'[.!?。！？]', text)
        # 清理句子并添加回标点符号
        cleaned_sentences = []
        punctuation_marks = re.findall(r'[.!?。！？]', text)
        
        for i, sentence in enumerate(sentences):
            if sentence.strip():  # 忽略空句子
                cleaned_sentence = sentence.strip()
                # 添加回标点符号（如果不是最后一句）
                if i < len(punctuation_marks):
                    cleaned_sentence += punctuation_marks[i]
                cleaned_sentences.append(cleaned_sentence)
                
        return cleaned_sentences if cleaned_sentences else [text]
    
    def _extract_knowledge_graph(self, chunks: List[str]) -> List[BearingFaultKnowledgeGraph]:
        """
        通过LLM从文本块中提取知识图谱数据
        
        Args:
            chunks: 分块后的文本列表
            
        Returns:
            知识图谱数据列表
        """
        # 导入LLM客户端
        try:
            from server.LLM_Client import LLMClient
            llm_client = LLMClient()
        except Exception as e:
            print(f"警告: 无法初始化LLM客户端: {e}")
            print("将返回空的知识图谱结果")
            return []
        
        # 为每个文本块调用LLM提取实体和关系
        kg_results = []
        previous_context = None
        
        for i, chunk in enumerate(chunks):
            try:
                # 创建高效的提示词
                prompt = self._create_efficient_prompt(chunk, previous_context)
                
                # 调用LLM提取知识图谱
                kg_data = llm_client.extract_knowledge_graph(prompt)
                kg_results.append(kg_data)
                
                # 提取关键信息作为下一个块的上下文
                previous_context = self._summarize_key_info(kg_data)
                
                print(f"已处理文本块 {i+1}/{len(chunks)}")
                
            except Exception as e:
                print(f"处理第 {i+1} 个文本块时出错: {e}")
                # 即使某个块处理失败，也继续处理其他块
                continue
        
        return kg_results
    
    def _create_efficient_prompt(self, text_chunk: str, previous_context: Optional[str] = None) -> str:
        """
        创建高效的提示词，确保不超过上下文长度限制并保留重要上下文信息
        
        Args:
            text_chunk: 当前文本块
            previous_context: 上下文信息（前一个块的关键信息摘要）
            
        Returns:
            构造好的提示词
        """
        
        # 构建基础提示词
        base_prompt = f"""你是一个专业的知识图谱构建助手。你的任务是从技术文档中提取结构化的轴承故障相关信息，
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
        if previous_context:
            context_prompt = f"""
重要上下文信息（请参考但不要重复提取）：
{previous_context}

请基于以上上下文信息和当前文档内容，提取新增的或不同的信息。
"""
            base_prompt += context_prompt
        
        return base_prompt
    
    def _summarize_key_info(self, kg_data: BearingFaultKnowledgeGraph) -> str:
        """
        从知识图谱数据中提取关键信息摘要，用于下一个文本块的上下文
        
        Args:
            kg_data: 知识图谱数据
            
        Returns:
            关键信息摘要
        """
        summary_parts = []
        
        # 提取已识别的实体类型和关键信息
        for entry in kg_data.entries:
            if entry.fault_type:
                summary_parts.append(f"故障类型: {entry.fault_type.name}")
            if entry.cause:
                summary_parts.append(f"故障原因: {entry.cause.name}")
            if entry.signal_feature:
                summary_parts.append(f"信号特征: {entry.signal_feature.name}")
            if entry.frequency:
                summary_parts.append(f"特征频率: {entry.frequency.name}")
            if entry.diagnosis_method:
                summary_parts.append(f"诊断方法: {entry.diagnosis_method.name}")
            if entry.influencing_factor:
                summary_parts.append(f"影响因素: {entry.influencing_factor.name}")
        
        # 限制摘要长度以避免占用过多上下文
        summary = "; ".join(summary_parts)
        if len(summary) > 500:  # 限制摘要长度
            summary = summary[:497] + "..."
            
        return summary if summary else "暂无关键信息"


class DocumentParser(ABC):
    """文档解析器抽象基类"""
    
    @abstractmethod
    def parse(self, file_path: str) -> str:
        """
        解析文档并返回纯文本内容
        
        Args:
            file_path: 文档文件路径
            
        Returns:
            解析后的纯文本内容
        """
        pass


class TextParser(DocumentParser):
    """纯文本解析器"""
    
    def parse(self, file_path: str) -> str:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()


class MarkdownParser(DocumentParser):
    """Markdown文档解析器"""
    
    def parse(self, file_path: str) -> str:
        # 对于简单的MD文件，直接读取文本内容
        # 复杂的MD解析可以使用markdown库处理
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()


class WordParser(DocumentParser):
    """Word文档解析器"""
    
    def parse(self, file_path: str) -> str:
        try:
            from docx import Document
        except ImportError:
            raise ImportError("请安装python-docx库: pip install python-docx")
        
        doc = Document(file_path)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        return '\n'.join(full_text)


# 使用示例
if __name__ == "__main__":
    # 创建文档处理器实例
    processor = DocumentProcessor()
    
    # 处理文档示例（需要实际的文件路径）
    # result = processor.process_document("path/to/your/document.md")
    # print(result)