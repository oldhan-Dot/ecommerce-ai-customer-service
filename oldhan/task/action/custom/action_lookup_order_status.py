from typing import Any, Dict

from oldhan.domain.state import DialogueState
from oldhan.task.action.base import Action, ActionResult
from oldhan.task.action.custom.shared import fetch_order, _build_order_summary


class LookupOrderStatusAction(Action):
    name = "action_lookup_order_status"
    async def run(self,state:DialogueState,args:Dict[str,Any])->ActionResult:
        #根据order_number查询订单的状态信息：order_status,order_summary
        order_number = state.active_task.slots.get("order_number")
        payload = await fetch_order(order_number)

#查询信息的几个action是将查询到的数据放在slot_updates中然后返回后更新到state的slots中
        if payload is None:
            return ActionResult(slot_updates={
                "order_status" : "查询失败",
                "order_summary": "暂时无法查到订单的信息,请稍后再试"
            })
        return ActionResult(slot_updates={
            "order_status":payload.get("order_status") or payload.get("status") or "未知",
            "order_summary":_build_order_summary(payload)
        })