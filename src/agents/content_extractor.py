"""
内容提取器 - 从 Agent 生成的 Markdown 中提取结构化数据

用于：
1. 从 Optimizer 输出中提取 P1/P2/P3 方案摘要
2. 从 Experimenter 输出中提取工单信息
"""
import re
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from loguru import logger


class ContentExtractor:
    """
    内容提取器
    
    从 Agent 生成的 Markdown 文本中提取结构化数据，
    用于前端显示卡片和提供下载功能。
    """
    
    @staticmethod
    def extract_optimization_plans(content: str) -> Optional[Dict[str, Any]]:
        """
        从 Optimizer 输出中提取优化方案摘要
        
        支持两种格式：
        1. 多方案格式：## P1 成分优化方案 / ## P2 结构优化方案 / ## P3 工艺优化方案
        2. 单方案格式：# 成分优化方案 / # 结构优化方案 / # 工艺优化方案
        
        Args:
            content: Optimizer Agent 生成的 Markdown 文本
            
        Returns:
            结构化的优化方案数据
        """
        # 检查是否包含优化方案相关内容
        has_optimization = any(kw in content for kw in ['优化方案', '成分优化', '结构优化', '工艺优化', 'P1', 'P2', 'P3'])
        if not content or not has_optimization:
            return None
            
        try:
            plans = {
                "type": "optimization_plans",
                "timestamp": datetime.now().isoformat(),
                "plans": []
            }
            
            # === 多方案格式提取（## P1/P2/P3） ===
            
            # 提取 P1 成分优化
            p1_match = re.search(
                r'##\s*P1[^#]*?成分优化[^#]*?\n(.*?)(?=##\s*P2|##\s*P3|---|\Z)', 
                content, 
                re.DOTALL | re.IGNORECASE
            )
            if p1_match:
                p1_content = p1_match.group(1)
                plan_name = ContentExtractor._extract_plan_name(p1_content)
                plans["plans"].append({
                    "id": "P1",
                    "name": plan_name or "成分优化方案",
                    "category": "成分优化",
                    "icon": "🎯",
                    "summary": ContentExtractor._extract_summary(p1_content, "成分"),
                    "key_changes": ContentExtractor._extract_table_changes(p1_content),
                    "expected_effect": ContentExtractor._extract_expected_effect(p1_content)
                })
            
            # 提取 P2 结构优化
            p2_match = re.search(
                r'##\s*P2[^#]*?结构优化[^#]*?\n(.*?)(?=##\s*P1|##\s*P3|---|\Z)', 
                content, 
                re.DOTALL | re.IGNORECASE
            )
            if p2_match:
                p2_content = p2_match.group(1)
                plan_name = ContentExtractor._extract_plan_name(p2_content)
                plans["plans"].append({
                    "id": "P2",
                    "name": plan_name or "结构优化方案",
                    "category": "结构优化",
                    "icon": "🏗️",
                    "summary": ContentExtractor._extract_summary(p2_content, "结构"),
                    "key_changes": ContentExtractor._extract_list_items(p2_content),
                    "expected_effect": ContentExtractor._extract_expected_effect(p2_content)
                })
            
            # 提取 P3 工艺优化
            p3_match = re.search(
                r'##\s*P3[^#]*?工艺优化[^#]*?\n(.*?)(?=##\s*P1|##\s*P2|##\s*综合|---|\Z)', 
                content, 
                re.DOTALL | re.IGNORECASE
            )
            if p3_match:
                p3_content = p3_match.group(1)
                plan_name = ContentExtractor._extract_plan_name(p3_content)
                plans["plans"].append({
                    "id": "P3",
                    "name": plan_name or "工艺优化方案",
                    "category": "工艺优化",
                    "icon": "⚡",
                    "summary": ContentExtractor._extract_summary(p3_content, "工艺"),
                    "key_changes": ContentExtractor._extract_table_changes(p3_content),
                    "expected_effect": ContentExtractor._extract_expected_effect(p3_content)
                })
            
            # === 单方案格式提取（# 成分/结构/工艺优化方案） ===
            if not plans["plans"]:
                # 单独的成分优化方案
                single_p1 = re.search(
                    r'#\s*成分优化方案\s*\n(.*?)(?=#\s*[^#]|\Z)', 
                    content, 
                    re.DOTALL | re.IGNORECASE
                )
                if single_p1:
                    p1_content = single_p1.group(1)
                    plan_name = ContentExtractor._extract_plan_name(p1_content)
                    plans["plans"].append({
                        "id": "P1",
                        "name": plan_name or "成分优化方案",
                        "category": "成分优化",
                        "icon": "🎯",
                        "summary": ContentExtractor._extract_summary(p1_content, "成分"),
                        "key_changes": ContentExtractor._extract_table_changes(p1_content),
                        "expected_effect": ContentExtractor._extract_expected_effect(p1_content)
                    })
                
                # 单独的结构优化方案
                single_p2 = re.search(
                    r'#\s*结构优化方案\s*\n(.*?)(?=#\s*[^#]|\Z)', 
                    content, 
                    re.DOTALL | re.IGNORECASE
                )
                if single_p2:
                    p2_content = single_p2.group(1)
                    plan_name = ContentExtractor._extract_plan_name(p2_content)
                    plans["plans"].append({
                        "id": "P2",
                        "name": plan_name or "结构优化方案",
                        "category": "结构优化",
                        "icon": "🏗️",
                        "summary": ContentExtractor._extract_summary(p2_content, "结构"),
                        "key_changes": ContentExtractor._extract_list_items(p2_content),
                        "expected_effect": ContentExtractor._extract_expected_effect(p2_content)
                    })
                
                # 单独的工艺优化方案
                single_p3 = re.search(
                    r'#\s*工艺优化方案\s*\n(.*?)(?=#\s*[^#]|\Z)', 
                    content, 
                    re.DOTALL | re.IGNORECASE
                )
                if single_p3:
                    p3_content = single_p3.group(1)
                    plan_name = ContentExtractor._extract_plan_name(p3_content)
                    plans["plans"].append({
                        "id": "P3",
                        "name": plan_name or "工艺优化方案",
                        "category": "工艺优化",
                        "icon": "⚡",
                        "summary": ContentExtractor._extract_summary(p3_content, "工艺"),
                        "key_changes": ContentExtractor._extract_table_changes(p3_content),
                        "expected_effect": ContentExtractor._extract_expected_effect(p3_content)
                    })
            
            # 提取推荐方案
            recommend_match = re.search(
                r'\*\*推荐方案[：:]\s*(P\d)\*\*',
                content,
                re.IGNORECASE
            )
            if recommend_match:
                plans["recommended"] = recommend_match.group(1)
            
            # 只有提取到方案才返回
            if plans["plans"]:
                logger.info(f"[ContentExtractor] 提取到 {len(plans['plans'])} 个优化方案")
                return plans
                
            return None
            
        except Exception as e:
            logger.error(f"[ContentExtractor] 提取优化方案失败: {e}")
            return None
    
    @staticmethod
    def _extract_plan_name(content: str) -> Optional[str]:
        """提取方案名称"""
        # 匹配 **方案名称：** xxx 或 **方案名称:** xxx
        name_match = re.search(
            r'\*\*方案名称[：:]\*\*\s*([^\n]+)',
            content
        )
        if name_match:
            name = name_match.group(1).strip()
            # 清理可能的引号和方括号
            name = re.sub(r'^[\[\]"\']+|[\[\]"\']+$', '', name)
            return name[:50] if name else None  # 限制长度
        return None
    
    @staticmethod
    def extract_workorder(content: str) -> Optional[Dict[str, Any]]:
        """
        从 Experimenter 输出中提取实验工单信息
        
        Args:
            content: Experimenter Agent 生成的 Markdown 文本
            
        Returns:
            结构化的工单数据
        """
        # 只有明确包含 "# 实验工单" 标题时才提取，避免误判
        if not content or not re.search(r'^#\s*实验工单', content, re.MULTILINE):
            return None
            
        try:
            # 系统自动生成工单编号和时间戳
            now = datetime.now()
            workorder = {
                "type": "workorder",
                "workorder_id": f"WO-{now.strftime('%Y%m%d')}-{now.strftime('%H%M%S')}",
                "timestamp": now.isoformat(),
                "generated_time": now.strftime('%Y-%m-%d %H:%M:%S'),
            }
            
            # 提取优化方案类型
            opt_match = re.search(r'优化方案[：:]\s*(P\d)', content)
            if opt_match:
                workorder["optimization_type"] = opt_match.group(1)
            
            # 提取方案名称
            plan_name_match = re.search(
                r'方案名称[：:]\s*([^\n]+)',
                content
            )
            if plan_name_match:
                plan_name = plan_name_match.group(1).strip()
                # 清理可能的引号和方括号
                plan_name = re.sub(r'^[\[\]"\']+|[\[\]"\']+$', '', plan_name)
                workorder["plan_name"] = plan_name[:60]
            
            # 提取实验目的
            purpose_match = re.search(
                r'##\s*实验目的\s*\n(.*?)(?=##|\Z)',
                content,
                re.DOTALL
            )
            if purpose_match:
                workorder["purpose"] = purpose_match.group(1).strip()[:200]
            
            # 提取成分配比表格
            composition = ContentExtractor._extract_composition_table(content)
            if composition:
                workorder["composition"] = composition
            
            # 提取工艺参数表格
            process_params = ContentExtractor._extract_process_table(content)
            if process_params:
                workorder["process_params"] = process_params
            
            # 提取预期结果
            expected = ContentExtractor._extract_expected_results(content)
            if expected:
                workorder["expected_results"] = expected
            
            # 存储完整 Markdown 用于下载
            workorder["full_content"] = content
            
            logger.info(f"[ContentExtractor] 提取工单: {workorder.get('workorder_id')}")
            return workorder
            
        except Exception as e:
            logger.error(f"[ContentExtractor] 提取工单失败: {e}")
            return None
    
    @staticmethod
    def _extract_summary(content: str, focus: str) -> str:
        """提取方案摘要"""
        # 尝试从"当前问题"部分提取
        problem_match = re.search(
            r'###\s*当前问题\s*\n(.*?)(?=###|\Z)',
            content,
            re.DOTALL
        )
        if problem_match:
            text = problem_match.group(1).strip()
            # 取第一句或前100字符
            first_line = text.split('\n')[0].strip()
            if first_line:
                return first_line[:100]
        
        return f"针对{focus}进行优化调整"
    
    @staticmethod
    def _extract_table_changes(content: str) -> List[Dict[str, str]]:
        """从表格中提取参数变化"""
        changes = []
        
        # 匹配表格行：| 参数 | 当前值 | 建议值 | ... |
        table_pattern = r'\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|'
        matches = re.findall(table_pattern, content)
        
        for match in matches:
            param, current, suggested = match
            param = param.strip()
            current = current.strip()
            suggested = suggested.strip()
            
            # 跳过表头
            if param in ['参数', '---', '元素'] or '---' in param:
                continue
            if current in ['当前值', '---'] or '---' in current:
                continue
                
            changes.append({
                "param": param,
                "from": current,
                "to": suggested
            })
        
        return changes[:5]  # 最多返回5项
    
    @staticmethod
    def _extract_list_items(content: str) -> List[Dict[str, str]]:
        """从列表中提取变化项"""
        changes = []
        
        # 匹配列表项：- xxx: yyy 或 - xxx → yyy
        list_pattern = r'-\s*([^:：→\n]+)[：:→]\s*([^\n]+)'
        matches = re.findall(list_pattern, content)
        
        for match in matches:
            param, value = match
            changes.append({
                "param": param.strip(),
                "to": value.strip()
            })
        
        return changes[:5]
    
    @staticmethod
    def _extract_expected_effect(content: str) -> str:
        """提取预期效果"""
        effect_match = re.search(
            r'###\s*预期效果\s*\n(.*?)(?=###|---|##|\Z)',
            content,
            re.DOTALL
        )
        if effect_match:
            text = effect_match.group(1).strip()
            # 合并多行为一行
            lines = [l.strip().lstrip('-').strip() for l in text.split('\n') if l.strip()]
            return '；'.join(lines[:3])
        
        return ""
    
    @staticmethod
    def _extract_composition_table(content: str) -> Dict[str, float]:
        """提取成分配比"""
        composition = {}
        
        # 查找成分配比部分
        comp_match = re.search(
            r'###\s*成分配比\s*\n(.*?)(?=###|\Z)',
            content,
            re.DOTALL
        )
        if not comp_match:
            return composition
            
        table_content = comp_match.group(1)
        
        # 匹配元素和含量
        patterns = [
            (r'\|\s*Al\s*\|\s*([\d.]+)', 'Al'),
            (r'\|\s*Ti\s*\|\s*([\d.]+)', 'Ti'),
            (r'\|\s*N\s*\|\s*([\d.]+)', 'N'),
        ]
        
        for pattern, element in patterns:
            match = re.search(pattern, table_content, re.IGNORECASE)
            if match:
                try:
                    composition[element] = float(match.group(1))
                except ValueError:
                    pass
        
        return composition
    
    @staticmethod
    def _extract_process_table(content: str) -> Dict[str, Any]:
        """提取工艺参数"""
        params = {}
        
        # 查找工艺参数部分
        proc_match = re.search(
            r'###\s*工艺参数\s*\n(.*?)(?=###|\Z)',
            content,
            re.DOTALL
        )
        if not proc_match:
            return params
            
        table_content = proc_match.group(1)
        
        # 匹配各参数
        patterns = [
            (r'沉积温度\s*\|\s*([\d.]+)', 'temperature'),
            (r'偏压\s*\|\s*-?([\d.]+)', 'bias_voltage'),
            (r'N₂流量\s*\|\s*([\d.]+)', 'n2_flow'),
            (r'Ar流量\s*\|\s*([\d.]+)', 'ar_flow'),
            (r'沉积时间\s*\|\s*([\d.]+)', 'deposition_time'),
        ]
        
        for pattern, key in patterns:
            match = re.search(pattern, table_content)
            if match:
                try:
                    params[key] = float(match.group(1))
                except ValueError:
                    pass
        
        return params
    
    @staticmethod
    def _extract_expected_results(content: str) -> Dict[str, Any]:
        """提取预期结果"""
        results = {}
        
        # 查找预期结果部分
        exp_match = re.search(
            r'##\s*预期结果\s*\n(.*?)(?=##|\Z)',
            content,
            re.DOTALL
        )
        if not exp_match:
            return results
            
        table_content = exp_match.group(1)
        
        # 匹配各指标
        patterns = [
            (r'硬度\s*\|\s*([\d.]+)', 'hardness'),
            (r'结合力\s*\|\s*([\d.]+)', 'adhesion'),
            (r'弹性模量\s*\|\s*([\d.]+)', 'elastic_modulus'),
        ]
        
        for pattern, key in patterns:
            match = re.search(pattern, table_content)
            if match:
                try:
                    results[key] = float(match.group(1))
                except ValueError:
                    pass
        
        return results


def extract_structured_content(content: str, agent_name: str) -> Optional[Dict[str, Any]]:
    """
    根据 Agent 类型提取结构化内容
    
    Args:
        content: Agent 生成的完整 Markdown 文本
        agent_name: Agent 名称（Optimizer/Experimenter）
        
    Returns:
        提取的结构化数据，如果无法提取返回 None
    """
    if not content or len(content) < 100:
        return None
    
    if agent_name == "Optimizer":
        return ContentExtractor.extract_optimization_plans(content)
    elif agent_name == "Experimenter":
        return ContentExtractor.extract_workorder(content)
    
    return None
