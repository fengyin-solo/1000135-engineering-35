"""出库管理接口：维护出库单，覆盖确认拣货、安排发运、取消出库等动作。"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.config import settings
from app.schemas import ActionResult, EntryPayload, PageResult
from app.services.outbound import OutboundService

router = APIRouter(prefix="/api/outbound", tags=["出库管理"])

service = OutboundService()

LIST_FIELDS = ["出库单号", "客户名称", "货物名称", "批次号", "出库数量", "出库温度", "拣货人", "出库时间"]
STATUSES = ["待拣货", "已拣货", "已发运", "已取消"]


@router.get("", response_model=PageResult[dict])
def list_entries(
    keyword: str | None = Query(default=None, description="按出库单号检索"),
    status: str | None = Query(default=None, description="待拣货、已拣货、已发运、已取消"),
    page: int = 1,
    size: int = settings.page_size_default,
) -> PageResult[dict]:
    """按出库单号与状态过滤出库管理列表；没有数据时返回空页，不报错。"""
    if size > settings.page_size_max:
        raise HTTPException(
            status_code=400,
            detail=f"每页最多 {settings.page_size_max} 条，请缩小分页范围",
        )
    items, total = service.list_entries(keyword=keyword, status=status, page=page, size=size)
    return PageResult(items=items, total=total, page=page, size=size)


@router.get("/{entry_id}", response_model=dict)
def get_entry(entry_id: int) -> dict:
    """读取单条出库单明细；不存在时给出可读的错误说明。"""
    entry = service.get_entry(entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"出库单 {entry_id} 不存在或已归档")
    return entry


@router.post("", response_model=ActionResult)
def create_entry(payload: EntryPayload) -> ActionResult:
    """登记一条出库单，缺字段时说明原因而不是静默丢弃。"""
    entry, missing = service.create_entry(payload.values)
    if missing:
        return ActionResult(ok=False, message=f"缺少必填字段：{'、'.join(missing)}")
    return ActionResult(ok=True, message="出库单已登记", entry=entry)


@router.post("/{entry_id}/actions", response_model=ActionResult)
def run_action(entry_id: int, payload: EntryPayload) -> ActionResult:
    """对单条出库单执行确认拣货、安排发运、取消出库；不允许的动作会被拦下并说明原因。"""
    action = str(payload.values.get("action") or "").strip()
    entry, message = service.run_action(entry_id, action)
    if entry is None:
        return ActionResult(ok=False, message=message)
    return ActionResult(ok=True, message=message, entry=entry)


@router.get("/export")
def export_entries() -> dict[str, Any]:
    """导出出库管理清单：返回当前过滤条件下的全量数据。"""
    items, total = service.list_entries(page=1, size=10000)
    return {"module": "outbound", "total": total, "items": items}
