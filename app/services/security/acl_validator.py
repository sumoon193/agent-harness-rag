"""
ACL 校验器。

校验工具权限和文档访问权限。
"""
from __future__ import annotations

import logging
from typing import Any

from app.schemas.enums import Visibility
from app.schemas.tool import ToolDefinition
from app.schemas.user import UserContext

logger = logging.getLogger(__name__)


class ACLValidator:
    """
    ACL 校验器。

    校验用户是否有权限执行特定操作。
    """

    def validate_tool_permission(
        self,
        tool: ToolDefinition,
        user: UserContext
    ) -> bool:
        """
        检查用户是否有权限调用工具。

        Args:
            tool: 工具定义
            user: 用户上下文

        Returns:
            是否有权限
        """
        # 检查权限范围
        if tool.permission_scope not in user.permissions:
            # 检查是否是 admin
            if user.role != "admin":
                logger.warning(
                    "tool_permission_denied",
                    extra={
                        "user_id": user.user_id,
                        "tool_name": tool.name,
                        "required_scope": tool.permission_scope
                    }
                )
                return False

        logger.debug(
            "tool_permission_granted",
            extra={"user_id": user.user_id, "tool_name": tool.name}
        )

        return True

    def validate_document_access(
        self,
        doc_acl: dict[str, Any],
        user: UserContext
    ) -> bool:
        """
        检查用户是否有权限访问文档。

        Args:
            doc_acl: 文档 ACL 元数据
            user: 用户上下文

        Returns:
            是否有权限
        """
        # 检查租户
        if doc_acl.get("tenant_id") != user.tenant_id:
            return False

        # 检查可见性
        visibility_str = doc_acl.get("visibility", "department")
        try:
            visibility = Visibility(visibility_str)
        except ValueError:
            visibility = Visibility.DEPARTMENT

        # public 表示同租户公开，不应再受部门边界限制
        if visibility == Visibility.PUBLIC:
            return True

        # 检查部门
        if doc_acl.get("department_id") not in user.department_ids:
            return False

        return self._check_visibility(visibility, doc_acl, user)

    def _check_visibility(
        self,
        visibility: Visibility,
        doc_acl: dict[str, Any],
        user: UserContext
    ) -> bool:
        """
        检查可见性权限。

        Args:
            visibility: 可见性级别
            doc_acl: 文档 ACL 元数据
            user: 用户上下文

        Returns:
            是否有权限
        """
        if visibility == Visibility.PUBLIC:
            return True

        if visibility == Visibility.DEPARTMENT:
            return True  # 已通过部门检查

        if visibility == Visibility.PRIVATE:
            # private 需要是 owner 或有特定权限
            owner_id = doc_acl.get("owner_user_id")
            if owner_id and owner_id == user.user_id:
                return True
            return "hr.document.private" in user.permissions or user.role == "admin"

        if visibility == Visibility.CONFIDENTIAL:
            # confidential 需要高级权限
            allowed_roles = doc_acl.get("allowed_roles", ["admin", "hr_manager"])
            return user.role in allowed_roles

        return False
