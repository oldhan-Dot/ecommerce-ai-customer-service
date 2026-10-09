from typing import Dict, Any

from oldhan.domain.messages import BotMessage, MessageObject
from oldhan.domain.state import DialogueState
from oldhan.task.action.base import Action, ActionResult
from oldhan.task.action.custom.shared import fetch_product


class RecommendSimilarProductsAction(Action):

    name = "action_recommend_similar_products"

    async def run(self, state:DialogueState, args:Dict[str,Any]) ->ActionResult:
        # 根据商品id查询类似商品（推荐系统）
        product_id = state.active_task.slots.get("product_id")
        label = product_id or "这件商品"

        payload = await fetch_product(product_id)
        if payload:
            label = str(payload.get("title") or "").strip() or label

        # text = (
        #     f"我已经收到你对\"{label}\"的相似商品推荐需求。"
        #     "不过当前版本还没有接入正式的推荐系统，稍后可以继续补上这部分能力。"
        # )
        # return ActionResult(messages=[BotMessage(text=text)])

        return ActionResult(
            messages=[
                BotMessage(text="好的，为你推荐的商品如下："),
                BotMessage(object=MessageObject(
                    type="product",
                    id="SKU-50012",
                    title="索尼 WH-1000XM5",
                    attributes={
                        "price": "2499.00",
                        "type": "头戴式",
                        "anc": "行业领先"
                    }
                )),
                BotMessage(object=MessageObject(
                    type="product",
                    id="SKU-50013",
                    title="索尼 WH-1000XM4",
                    attributes={
                        "price": "1999.00",
                        "type": "头戴式",
                        "anc": "行业领先"
                    }
                )),
                BotMessage(object=MessageObject(
                    type="product",
                    id="SKU-50014",
                    title="索尼 WH-1000XM3",
                    attributes={
                        "price": "1499.00",
                        "type": "头戴式",
                        "anc": "行业领先"
                    }
                ))
            ]
        )