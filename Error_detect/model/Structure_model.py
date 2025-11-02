from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field

class SeverityLevel(str, Enum):
    mild = "mild"
    moderate = "moderate"
    severe = "severe"

# ======================
# 核心实体模型
# ======================

class BearingFaultType(BaseModel):
    """轴承故障类型实体"""
    name: str = Field(..., description="故障类型名称，如'疲劳剥落'、'磨损'、'胶合'等")
    severity: Optional[SeverityLevel] = Field(None, description="故障严重程度")
    caused_by: List[str] = Field(default_factory=list, description="导致该故障的原因列表（关联FaultCause.name）")
    manifests_as: List[str] = Field(default_factory=list, description="在信号中的表现形式（关联SignalFeature.name）")
    has_feature_frequency: List[str] = Field(default_factory=list, description="对应的特征频率（关联CharacteristicFrequency.name）")
    detected_by: List[str] = Field(default_factory=list, description="可检测该故障的诊断方法（关联DiagnosisMethod.name")


class FaultCause(BaseModel):
    """故障原因实体"""
    name: str = Field(..., description="原因名称，如'润滑不良'、'超负荷'、'装配不当'等")
    produces: List[str] = Field(default_factory=list, description="该原因导致的故障类型（关联BearingFaultType.name）")
    effect_description: Optional[str] = Field(None, description="对振动或诊断的具体影响描述")


class SignalFeature(BaseModel):
    """故障特征信号实体"""
    name: str = Field(..., description="信号特征名称，如'周期性冲击'、'边频带'、'包络调制'等")
    frequency_band: Optional[str] = Field(None, description="所属频段，如'高频（10–60 kHz）'")
    associated_faults: List[str] = Field(default_factory=list, description="关联的故障类型（BearingFaultType.name）")
    influenced_by: List[str] = Field(default_factory=list, description="受哪些影响因素干扰（关联InfluencingFactor.name）")


class CharacteristicFrequency(BaseModel):
    """特征频率实体"""
    name: str = Field(..., description="频率名称，如'外圈通过频率'、'滚动体自转频率'等")
    formula: Optional[str] = Field(None, description="计算公式，如 'f_outer = (Z/2) * f0 * (1 - d/D * cosα)'")
    depends_on: List[str] = Field(default_factory=list, description="依赖的参数，如['轴转频 f0', '滚动体数 Z', ...]")
    associated_fault: Optional[str] = Field(None, description="对应的故障类型（BearingFaultType.name）")


class DiagnosisMethod(BaseModel):
    """诊断方法实体"""
    name: str = Field(..., description="方法名称，如'共振解调'、'小波分析'、'包络分析'等")
    frequency_band: Optional[str] = Field(None, description="适用频段")
    advantage: Optional[str] = Field(None, description="方法优势")
    limitation: Optional[str] = Field(None, description="方法局限性")
    detects_faults: List[str] = Field(default_factory=list, description="可检测的故障类型（BearingFaultType.name）")
    influenced_by: List[str] = Field(default_factory=list, description="受哪些因素影响（InfluencingFactor.name）")


class InfluencingFactor(BaseModel):
    """影响因素实体"""
    name: str = Field(..., description="因素名称，如'转速'、'测点位置'、'润滑状态'等")
    effect_description: Optional[str] = Field(None, description="对诊断或信号的具体影响")
    influences: List[str] = Field(default_factory=list, description="影响的实体，如诊断方法、信号特征等（通过名称关联）")


# ======================
# 顶层知识图谱条目（用于批量解析）
# ======================

class BearingFaultKnowledgeGraphEntry(BaseModel):
    """单条轴承故障知识图谱结构化条目"""
    fault_type: Optional[BearingFaultType] = None
    cause: Optional[FaultCause] = None
    signal_feature: Optional[SignalFeature] = None
    frequency: Optional[CharacteristicFrequency] = None
    diagnosis_method: Optional[DiagnosisMethod] = None
    influencing_factor: Optional[InfluencingFactor] = None


# ======================
# 批量输出模型（用于一次解析多个条目）
# ======================

class BearingFaultKnowledgeGraph(BaseModel):
    """完整的轴承故障知识图谱结构化输出"""
    entries: List[BearingFaultKnowledgeGraphEntry] = Field(
        ..., description="结构化知识条目列表"
    )


import json

# ======================
# JSON输出解析器
# ======================

class JsonOutputParser:
    """JSON输出解析器"""
    def __init__(self, pydantic_object):
        self.pydantic_object = pydantic_object
    
    def parse(self, text: str):
        """解析LLM返回的JSON格式输出"""
        import re
        
        try:
            # 尝试直接解析JSON
            data = json.loads(text)
            return self.pydantic_object(**data)
        except json.JSONDecodeError:
            # 如果直接解析失败，尝试从文本中提取JSON部分
            # 查找第一个 '{' 和最后一个 '}' 之间的内容
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                try:
                    json_str = match.group(0)
                    data = json.loads(json_str)
                    return self.pydantic_object(**data)
                except json.JSONDecodeError:
                    pass
            
            # 如果解析失败，返回空的知识图谱
            return self.pydantic_object(entries=[])
    
    def get_format_instructions(self):
        """获取格式说明"""
        # 生成Pydantic模型的JSON模式
        schema = self.pydantic_object.model_json_schema()
        return json.dumps(schema, indent=2, ensure_ascii=False)

# 创建解析器实例（可直接用于 LLM 输出解析）
parser = JsonOutputParser(pydantic_object=BearingFaultKnowledgeGraph)

# 获取格式指示（用于 prompt 中）
format_instructions = parser.get_format_instructions()

