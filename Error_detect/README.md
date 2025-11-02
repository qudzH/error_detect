# 轴承故障诊断文档处理系统

这是一个用于处理多种格式文档（MD、TXT、Word等），并通过大语言模型（LLM）提取结构化知识图谱数据的Python模块。该系统提供Web界面，方便用户上传文档并查看处理结果。

## 功能特性

1. **多格式文档支持**：支持MD、TXT、Word(.docx)等常见文档格式
2. **智能文本解析**：自动解析文档内容并提取纯文本
3. **上下文感知分块**：智能地将长文档分割成适合LLM处理的块，同时保持语义完整性
4. **高效提示词工程**：优化提示词设计，确保不超过LLM上下文长度限制，并有效保留上下文信息
5. **知识图谱提取**：通过LLM从文档中提取结构化的实体和关系信息
6. **错误处理与容错**：具备良好的错误处理机制，即使部分文本块处理失败也不会影响整体流程

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 基本用法

```python
python main.py
```

### 配置LLM客户端

要使用LLM功能，需要设置相应的API密钥等：

```bash
API_KEY = 'your_api_key'
BASE_URL = 'your_base_url'
MODEL_NAME = 'your_model_name'
```

## 项目结构

```
.
├── router
	├── process_router.py  		  # api接口
├── server 
	├── document_processor.py     # 文档处理主模块
	├── LLM_Client.py             # LLM客户端模块
├── model
	├── Structure_model.py        # 知识图谱数据结构定义
├── requirements.txt         	  # 项目依赖
├── main.py                       # 主函数
└── README.md                     # 项目说明文档

```

## 核心组件说明

### DocumentProcessor（文档处理器）

主类，负责整个文档处理流程：
- 接收多种格式的文档
- 解析文档内容
- 智能分块处理
- 调用LLM提取知识图谱

### LLM_Client（LLM客户端）

负责与大语言模型交互：
- 构造高效的提示词
- 调用LLM API
- 解析LLM输出为结构化数据

### Structure_model（结构模型）

定义知识图谱的数据结构：
- 实体类型定义（故障类型、原因、信号特征等）
- 关系类型定义
- JSON序列化/反序列化支持

## 高效提示词设计方案

为了确保提示词不超过LLM上下文长度限制并有效保留上下文信息，采用了以下策略：

1. **智能分块算法**：
   - 按段落优先分割
   - 超长段落再按句子分割
   - 尽量保持语义完整性

2. **上下文传递机制**：
   - 为每个文本块提取关键信息摘要
   - 将摘要作为上下文传递给下一个块的处理
   - 避免重复提取相同信息

3. **提示词优化**：
   - 明确的任务指令
   - 结构化的输出格式要求
   - 上下文信息的有效整合

## 扩展支持

### 添加新的文档格式

可以通过继承`DocumentParser`抽象基类来添加新的文档格式支持：

```python
from document_processor import DocumentParser

class PDFParser(DocumentParser):
    def parse(self, file_path: str) -> str:
        # 实现PDF解析逻辑
        pass

# 注册新的解析器
processor.add_parser('.pdf', PDFParser())
```

### 自定义知识图谱结构

可以根据具体领域需求修改`Structure_model.py`中的数据结构定义。

## 启动Web界面

系统提供了一个基于FastAPI的Web界面，可以通过以下步骤启动：

1. 确保已安装所有依赖：
```bash
pip install -r requirements.txt
```

2. 启动服务器：
```bash
python main.py
```

3. 在浏览器中访问 `http://localhost:8000` 查看Web界面

4. 通过Web界面上传文档并查看处理结果

## Web界面功能

- 支持拖拽上传文档
- 支持MD、TXT、DOCX格式
- 实时显示处理进度
- 可视化展示文本内容和分块结果
- 结构化显示知识图谱数据

## 注意事项

1. 使用LLM功能需要有效的API密钥
2. 处理大型文档可能消耗较多时间和API额度
3. 确保系统有足够的内存来处理大型文档
4. 根据实际使用的LLM调整最大上下文长度参数