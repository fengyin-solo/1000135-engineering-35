"""批次追溯接口：维护追溯记录，覆盖关联上游、发布追溯、撤回追溯等动作。"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.config import settings
from app.schemas import ActionResult, EntryPayload, PageResult
from app.services.trace import TraceService

router = APIRouter(prefix="/api/trace", tags=["批次追溯"])

service = TraceService()

LIST_FIELDS = ["追溯码", "货物名称", "生产批次", "上游供应商", "入库单号", "全程温度区间", "追溯状态"]
STATUSES = ["待关联", "已关联", "已发布", "已撤回"]


@router.get("", response_model=PageResult[dict])
def list_entries(
    keyword: str | None = Query(default=None, description="按追溯码检索"),
    status: str | None = Query(default=None, description="待关联、已关联、已发布、已撤回"),
    page: int = 1,
    size: int = settings.page_size_default,
) -> PageResult[dict]:
    """按追溯码与状态过滤批次追溯列表；没有数据时返回空页，不报错。"""
    if size > settings.page_size_max:
        raise HTTPException(status_code=400, detail=f"每页最多 {settings.page_size_max} 条，请缩小分页范围")
    items, total = service.list_entries(keyword=keyword, status=status, page=page, size=size)
    return PageResult(items=items, total=total, page=page, size=size)


@router.get("/{entry_id}", response_model=dict)
def get_entry(entry_id: int) -> dict:
    """读取单条追溯记录明细；不存在时给出可读的错误说明。"""
    entry = service.get_entry(entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"追溯记录 {entry_id} 不存在或已归档")
    return entry


@router.post("", response_model=ActionResult)
def create_entry(payload: EntryPayload) -> ActionResult:
    """登记一条追溯记录，缺字段时说明原因而不是静默丢弃。"""
    entry, missing = service.create_entry(payload.values)
    if missing:
        return ActionResult(ok=False, message=f"缺少必填字段：{'、'.join(missing)}")
    return ActionResult(ok=True, message="追溯记录已登记", entry=entry)


@router.post("/{entry_id}/actions", response_model=ActionResult)
def run_action(entry_id: int, payload: EntryPayload) -> ActionResult:
    """对单条追溯记录执行关联上游、发布追溯、撤回追溯；不允许的动作会被拦下并说明原因。"""
    action = str(payload.values.get("action") or "").strip()
    entry, message = service.run_action(entry_id, action)
    if entry is None:
        return ActionResult(ok=False, message=message)
    return ActionResult(ok=True, message=message, entry=entry)


@router.get("/export")
def export_entries() -> dict[str, Any]:
    """导出批次追溯清单：返回当前过滤条件下的全量数据。"""
    items, total = service.list_entries(page=1, size=10000)
    return {"module": "trace", "total": total, "items": items}
