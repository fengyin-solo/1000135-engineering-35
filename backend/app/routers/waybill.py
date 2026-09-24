"""运单管理接口：维护冷链运单，覆盖确认装车、签收运单、作废运单等动作。"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.config import settings
from app.schemas import ActionResult, EntryPayload, PageResult
from app.services.waybill import WaybillService

router = APIRouter(prefix="/api/waybill", tags=["运单管理"])

service = WaybillService()

LIST_FIELDS = ["运单号", "关联订单", "承运车辆", "司机姓名", "装车时间", "卸货时间", "运单状态"]
STATUSES = ["待装车", "运输中", "已签收", "已作废"]


@router.get("", response_model=PageResult[dict])
def list_entries(
    keyword: str | None = Query(default=None, description="按运单号检索"),
    status: str | None = Query(default=None, description="待装车、运输中、已签收、已作废"),
    page: int = 1,
    size: int = settings.page_size_default,
) -> PageResult[dict]:
    """按运单号与状态过滤运单管理列表；没有数据时返回空页，不报错。"""
    if size > settings.page_size_max:
        raise HTTPException(status_code=400, detail=f"每页最多 {settings.page_size_max} 条，请缩小分页范围")
    items, total = service.list_entries(keyword=keyword, status=status, page=page, size=size)
    return PageResult(items=items, total=total, page=page, size=size)


@router.get("/{entry_id}", response_model=dict)
def get_entry(entry_id: int) -> dict:
    """读取单条冷链运单明细；不存在时给出可读的错误说明。"""
    entry = service.get_entry(entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"冷链运单 {entry_id} 不存在或已归档")
    return entry


@router.post("", response_model=ActionResult)
def create_entry(payload: EntryPayload) -> ActionResult:
    """登记一条冷链运单，缺字段时说明原因而不是静默丢弃。"""
    entry, missing = service.create_entry(payload.values)
    if missing:
        return ActionResult(ok=False, message=f"缺少必填字段：{'、'.join(missing)}")
    return ActionResult(ok=True, message="冷链运单已登记", entry=entry)


@router.post("/{entry_id}/actions", response_model=ActionResult)
def run_action(entry_id: int, payload: EntryPayload) -> ActionResult:
    """对单条冷链运单执行确认装车、签收运单、作废运单；不允许的动作会被拦下并说明原因。"""
    action = str(payload.values.get("action") or "").strip()
    entry, message = service.run_action(entry_id, action)
    if entry is None:
        return ActionResult(ok=False, message=message)
    return ActionResult(ok=True, message=message, entry=entry)


@router.get("/export")
def export_entries() -> dict[str, Any]:
    """导出运单管理清单：返回当前过滤条件下的全量数据。"""
    items, total = service.list_entries(page=1, size=10000)
    return {"module": "waybill", "total": total, "items": items}
