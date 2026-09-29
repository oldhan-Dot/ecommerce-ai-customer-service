from typing import Dict, Any

from oldhan.domain.state import DialogueState
from oldhan.task.action.base import Action, ActionResult
from oldhan.task.action.custom.shared import fetch_logistics


class LookupOrderLogisticACtion(Action):
    name = "action_lookup_order_logistic"
    async def run(self,state:DialogueState,args:Dict[str,Any]) ->ActionResult:
        #根据订单编号查询订单物流信息：logistics_company,tracking_number,logistic_status
        order_number = state.active_task.slots.get("order_number")
        payload = await fetch_logistics(order_number)

        if payload is None:
            return ActionResult(
                slots_updates={
                    "tracking_number":"未知",
                    "logistics_company": "未知",
                    "logistics_status": "暂时无法查到物流信息，请稍后再试。",
                }
            )
        return ActionResult(
            slots_updates={
                "tracking_number":payload.get("tracking_number") or "未知",
                "logistics_company":payload.get("logistics_company"),
                "logistics_status":payload.get("logistics_status") or payload.get("status") or "未知",
            }
        )