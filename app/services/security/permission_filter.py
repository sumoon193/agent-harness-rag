"""
权限过滤器。

按 tenant_id, department_id, visibility 过滤 chunks 和 citations。
"""
from __future__ import annotations

import logging
from typing import Any

from app.schemas.chunk import ChunkCreate, Citation
from app.schemas.enums import Visibility
from app.schemas.user import UserContext

logger = logging.getLogger(__name__)


class PermissionFilter:
    """
    权限过滤器。

    实现三层权限控制的检索前过滤。
    """

    def filter_chunks(
        self,
        chunks: list[ChunkCreate],
        user: UserContext
    ) -> list[ChunkCreate]:
        """
        过滤 chunks。

        按 tenant_id, department_id, visibility 过滤。

        Args:
            chunks: 分块列表
            user: 用户上下文

        Returns:
            过滤后的分块列表
        """
        logger.info(
            "filtering_chunks",
            extra={"input_count": len(chunks), "user_id": user.user_id}
        )

        filtered = []
        for chunk in chunks:
            if self._check_access(chunk, user):
                filtered.append(chunk)
            else:
                logger.debug(
                    "chunk_filtered_out",
                    extra={
                        "chunk_id": chunk.document_id,
                        "chunk_tenant": chunk.tenant_id,
                        "chunk_dept": chunk.department_id,
                        "chunk_visibility": chunk.visibility.value if hasattr(chunk.visibility, 'value') else chunk.visibility
                    }
                )

        logger.info(
            "chunks_filtered",
            extra={"input_count": len(chunks), "output_count": len(filtered)}
        )

        return filtered

    def filter_citations(
        self,
        citations: list[Citation],
        user: UserContext,
        metadata_map: dict[int, dict[str, Any]] | None = None
    ) -> list[Citation]:
        """
        过滤 citations。

        答案生成前二次校验，确保用户有权限看到引用。

        Args:
            citations: 引用列表
            user: 用户上下文
            metadata_map: 引用 ID 到 ACL 元数据的映射（可选）

        Returns:
            过滤后的引用列表
        """
        if metadata_map is None:
            # 没有元数据映射，返回全部（信任上游）
            return citations

        filtered = []
        for citation in citations:
            meta = metadata_map.get(citation.id)
            if meta and self._check_access_by_meta(meta, user):
                filtered.append(citation)

        return filtered

    def _check_access(self, chunk: ChunkCreate, user: UserContext) -> bool:
        """
        检查用户是否有权限访问 chunk。

        Args:
            chunk: 分块
            user: 用户上下文

        Returns:
            是否有权限
        """
        # 检查租户
        if chunk.tenant_id != user.tenant_id:
            return False

        # public 表示同租户公开，不应再受部门边界限制
        if chunk.visibility == Visibility.PUBLIC:
            return True

        # 检查部门
        if chunk.department_id not in user.department_ids:
            return False

        # 检查可见性
        return self._check_visibility(chunk.visibility, user, chunk)

    def _check_access_by_meta(self, meta: dict[str, Any], user: UserContext) -> bool:
        """
        检查用户是否有权限访问（基于元数据）。

        Args:
            meta: ACL 元数据
            user: 用户上下文

        Returns:
            是否有权限
        """
        # 检查租户
        if meta.get("tenant_id") != user.tenant_id:
            return False

        # 检查可见性
        visibility_str = meta.get("visibility", "department")
        try:
            visibility = Visibility(visibility_str)
        except ValueError:
            visibility = Visibility.DEPARTMENT

        # public 表示同租户公开，不应再受部门边界限制
        if visibility == Visibility.PUBLIC:
            return True

        # 检查部门
        if meta.get("department_id") not in user.department_ids:
            return False

        return self._check_visibility(visibility, user)

    def _check_visibility(self, visibility: Visibility, user: UserContext, chunk: ChunkCreate | None = None) -> bool:
        """
        检查可见性权限。

        Args:
            visibility: 可见性级别
            user: 用户上下文
            chunk: 分块（可选，用于检查 owner）

        Returns:
            是否有权限
        """
        if visibility == Visibility.PUBLIC:
            return True

        if visibility == Visibility.DEPARTMENT:
            return True  # 已通过部门检查

        if visibility == Visibility.PRIVATE:
            # private 需要是 owner 或有特定权限
            if chunk and chunk.acl_metadata:
                owner_id = chunk.acl_metadata.get("owner_user_id")
                if owner_id and owner_id == user.user_id:
                    return True
            return "hr.document.private" in user.permissions or user.role == "admin"

        if visibility == Visibility.CONFIDENTIAL:
            # confidential 需要高级权限
            return user.role in ["admin", "hr_manager"]

        return False
