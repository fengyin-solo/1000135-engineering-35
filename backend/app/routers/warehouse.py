"""冷库管理接口：维护冷库档案，覆盖启用冷库、安排检修、停用冷库等动作。"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.config import settings
from app.schemas import ActionResult, EntryPayload, PageResult
from app.services.warehouse import WarehouseService

router = APIRouter(prefix="/api/warehouse", tags=["冷库管理"])

service = WarehouseService()

LIST_FIELDS = ["冷库编码", "冷库名称", "库区温区", "设定温度", "库容吨位", "责任人", "启用状态"]
STATUSES = ["已启用", "检修中", "已停用"]


@router.get("", response_model=PageResult[dict])
def list_entries(
    keyword: str | None = Query(default=None, description="按冷库编码检索"),
    status: str | None = Query(default=None, description="已启用、检修中、已停用"),
    page: int = 1,
    size: int = settings.page_size_default,
) -> PageResult[dict]:
    """按冷库编码与状态过滤冷库管理列表；没有数据时返回空页，不报错。"""
    if size > settings.page_size_max:
        raise HTTPException(
            status_code=400,
            detail=f"每页最多 {settings.page_size_max} 条，请缩小分页范围",
        )
    items, total = service.list_entries(keyword=keyword, status=status, page=page, size=size)
    return PageResult(items=items, total=total, page=page, size=size)


@router.get("/{entry_id}", response_model=dict)
def get_entry(entry_id: int) -> dict:
    """读取单条冷库档案明细；不存在时给出可读的错误说明。"""
    entry = service.get_entry(entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"冷库档案 {entry_id} 不存在或已归档")
    return entry


@router.post("", response_model=ActionResult)
def create_entry(payload: EntryPayload) -> ActionResult:
    """登记一条冷库档案，缺字段时说明原因而不是静默丢弃。"""
    entry, missing = service.create_entry(payload.values)
    if missing:
        return ActionResult(ok=False, message=f"缺少必填字段：{'、'.join(missing)}")
    return ActionResult(ok=True, message="冷库档案已登记", entry=entry)


@router.post("/{entry_id}/actions", response_model=ActionResult)
def run_action(entry_id: int, payload: EntryPayload) -> ActionResult:
    """对单条冷库档案执行启用冷库、安排检修、停用冷库；不允许的动作会被拦下并说明原因。"""
    action = str(payload.values.get("action") or "").strip()
    entry, message = service.run_action(entry_id, action)
    if entry is None:
        return ActionResult(ok=False, message=message)
    return ActionResult(ok=True, message=message, entry=entry)


@router.get("/export")
def export_entries() -> dict[str, Any]:
    """导出冷库管理清单：返回当前过滤条件下的全量数据。"""
    items, total = service.list_entries(page=1, size=10000)
    return {"module": "warehouse", "total": total, "items": items}
