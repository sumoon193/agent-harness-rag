"""
HR 清单生成工具。

根据场景生成 HR 清单。
"""
from __future__ import annotations

import logging
from typing import Any

from app.schemas.user import UserContext

logger = logging.getLogger(__name__)


class HRChecklistHandler:
    """
    HR 清单生成工具处理器。

    根据场景（入职/转正/报销/请假）生成对应的清单。
    """

    # 模拟清单数据
    CHECKLISTS: dict[str, list[dict[str, Any]]] = {
        "入职": [
            {"step": 1, "title": "提交入职材料", "description": "身份证、学历证明、离职证明", "deadline": "入职前 3 天"},
            {"step": 2, "title": "签署劳动合同", "description": "HR 会安排签署", "deadline": "入职当天"},
            {"step": 3, "title": "领取办公设备", "description": "笔记本电脑、工牌等", "deadline": "入职当天"},
            {"step": 4, "title": "开通系统账号", "description": "邮箱、OA、代码仓库等", "deadline": "入职后 1 天"},
            {"step": 5, "title": "参加入职培训", "description": "公司文化、规章制度", "deadline": "入职后 3 天内"},
        ],
        "转正": [
            {"step": 1, "title": "完成试用期考核", "description": "直属主管填写考核表", "deadline": "转正前 7 天"},
            {"step": 2, "title": "转正面谈", "description": "与直属主管面谈", "deadline": "转正前 5 天"},
            {"step": 3, "title": "提交转正申请", "description": "在 OA 系统提交", "deadline": "转正前 3 天"},
            {"step": 4, "title": "HR 审批", "description": "HR 审核转正材料", "deadline": "转正前 1 天"},
            {"step": 5, "title": "完成转正", "description": "薪资调整、福利变更", "deadline": "转正当天"},
        ],
        "报销": [
            {"step": 1, "title": "整理发票", "description": "确保发票真实有效", "deadline": "报销前"},
            {"step": 2, "title": "填写报销单", "description": "在 OA 系统填写", "deadline": "报销当天"},
            {"step": 3, "title": "直属主管审批", "description": "主管审核报销单", "deadline": "报销后 1 天"},
            {"step": 4, "title": "财务审核", "description": "财务审核发票和金额", "deadline": "报销后 3 天"},
            {"step": 5, "title": "报销到账", "description": "打款到工资卡", "deadline": "报销后 5-7 天"},
        ],
        "请假": [
            {"step": 1, "title": "提前申请", "description": "事假提前 1 天，年假提前 3 天", "deadline": "请假前"},
            {"step": 2, "title": "填写请假单", "description": "在 OA 系统填写", "deadline": "请假当天"},
            {"step": 3, "title": "直属主管审批", "description": "主管审核请假申请", "deadline": "请假前"},
            {"step": 4, "title": "工作交接", "description": "与同事交接工作", "deadline": "请假前"},
            {"step": 5, "title": "销假", "description": "返回后在 OA 系统销假", "deadline": "返岗当天"},
        ],
    }

    async def execute(
        self,
        parameters: dict[str, Any],
        user_context: UserContext
    ) -> dict[str, Any]:
        """
        生成 HR 清单。

        Args:
            parameters: 工具参数
                - scenario: 场景（入职/转正/报销/请假）
            user_context: 用户上下文

        Returns:
            清单内容
        """
        scenario = parameters.get("scenario", "入职")

        logger.info(
            "hr_checklist_generated",
            extra={"scenario": scenario, "user_id": user_context.user_id}
        )

        # 获取清单
        checklist = self.CHECKLISTS.get(scenario, self.CHECKLISTS["入职"])

        return {
            "scenario": scenario,
            "checklist": checklist,
            "total_steps": len(checklist),
            "estimated_duration": "5-7 个工作日"
        }
