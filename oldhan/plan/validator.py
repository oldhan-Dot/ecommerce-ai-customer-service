from oldhan.clarify.reasons import ClarifyReason
from oldhan.domain.state import DialogueState
from oldhan.knowledge.intents import KnowledgeIntent
from oldhan.plan.models import TurnPlan, TurnPlanValidationResult, TaskTurnPlan


#将TurnPlan意图识别的结果进行结构化校验

class TurnPlanValidator:

    def validate(
            self,
            turn_plan:TurnPlan,
            state:DialogueState,
            knowledge_intents:dict[str,KnowledgeIntent]
    )->TurnPlanValidationResult:
        # 1.单轨道校验
        # 获取轨道信息
        tracks:list[str] = []  # ["task","knowledeg"]
        if turn_plan.task is not None:
            tracks.append("task")
        if turn_plan.knowledge is not None:
            tracks.append("knowledge")
        if turn_plan.chitchat is not None:
            tracks.append("chitchat")
        # 校验轨道
        if len(tracks)==0:
            return TurnPlanValidationResult(valid=False, reason=ClarifyReason.MISSING_TRACK)
        if len(tracks)>1:
            return TurnPlanValidationResult(valid=False, reason=ClarifyReason.MULTIPLE_TRACKS)
        # 2.轨道内容校验
        if tracks[0]=="task":
            # 进行任务轨道的命令校验
            return self._validate_task(turn_plan)
        elif tracks[0] == "knowledge":
            # 进行知识轨道的intents校验
            return self._validate_knowledge(turn_plan,state,knowledge_intents)
        else:
            return TurnPlanValidationResult(valid=True)

    def _validate_task(self, turn_plan:TurnPlan)->TurnPlanValidationResult:
        task_turn_plan:TaskTurnPlan = turn_plan.task
        if not task_turn_plan.commands:
            return TurnPlanValidationResult(
                valid=False,
                reason=ClarifyReason.MISSING_TASK_COMMANDS
            )
        return  TurnPlanValidationResult(valid=True)

    def _validate_knowledge(self, turn_plan:TurnPlan, state:DialogueState, knowledge_intents:dict[str,KnowledgeIntent])->TurnPlanValidationResult:
        knowledge_turn_plan = turn_plan.knowledge
        if not knowledge_turn_plan.intents:
            return TurnPlanValidationResult(
                valid=False,
                reason=ClarifyReason.MISSING_KNOWLEDGE_INTENT
            )

        for intent_id in knowledge_turn_plan.intents:
            intent = knowledge_intents[intent_id]
            requires_object = intent.requires_object
            if requires_object is not None:
                if state.focused_object and state.focused_object.type == requires_object:
                    return TurnPlanValidationResult(
                        valid=False,
                        reason=ClarifyReason.MISSING_FOCUSED_OBJECT
                    )

        return TurnPlanValidationResult(valid=True)
