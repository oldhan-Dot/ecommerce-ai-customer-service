from pipes import quote
from typing import Dict, Any

from oldhan.conf.config import settings
from oldhan.domain.state import DialogueState
from oldhan.infrastructure import http_util
from oldhan.task.action.base import Action, ActionResult


class SubmitRefundRequestAction(Action):

    name = "action_submit_refund_request"

    async def run(self, state:DialogueState, args:Dict[str,Any]) ->ActionResult:
        # 1.从当前任务上下文的slots中获取订单编号与退款原因
        order_number = state.active_task.slots.get("order_number")
        refund_reason = state.active_task.slots.get("refund_reason")

        # 2.调用业务后端创建退款申请
        url = f"{settings.commerce_api_base_url.rstrip('/')}/orders/{quote(order_number)}/refund-applications"
        try:
            response = await http_util.http_client.post(url, json={"reason": refund_reason or "", "submitted_by": "system"})
            result = response.json()
            print(result)
        except Exception:
            return ActionResult(slot_updates={
                "order_submit_status": "error",
            })

        # 3.根据返回结果设置退款状态
        if result.get("code") == 0:
            print(f"~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~success")
            return ActionResult(slot_updates={
                "tips": f"好的，订单{order_number}的退款申请已提交，原因是：{refund_reason}。后续会尽快为你处理。",
            })
        else:
            print(f"~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~error")
            return ActionResult(slot_updates={
                "tips": f"抱歉，订单{order_number}的退款申请提交失败，请联系人工客服。",
            })
