"""Interview agent orchestrator with true agentic flow.

Provides AgenticInterviewAgent - a true agent with reasoning loop and tool use.
"""

import json
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlmodel import Session, select

from backend.models import InterviewSession, InterviewTurn, QuestionBank
from backend.schemas import InterviewNextRequest
from backend.services.agent_context import AgentContext, build_context_from_request
from backend.services.agent_reasoning import AgentReasoningLoop, AgentDecision

logger = logging.getLogger(__name__)


def _load_state(interview_session: InterviewSession) -> Dict[str, Any]:
    state = json.loads(interview_session.conversation_state_json or "{}")
    return {
        "current_question_id": state.get("current_question_id"),
        "followup_count": state.get("followup_count", 0),
        "question_index": state.get("question_index", 0),
        "initial_answer_score": state.get("initial_answer_score", 0),
        "previous_followups": state.get("previous_followups", []),
    }


def _save_state(interview_session: InterviewSession, state: Dict[str, Any], session: Session) -> None:
    interview_session.conversation_state_json = json.dumps(state)
    session.add(interview_session)
    session.commit()


def _get_last_main_turn(session_id: str, session: Session) -> Optional[InterviewTurn]:
    return session.exec(
        select(InterviewTurn)
        .where(InterviewTurn.session_id == session_id)
        .where(InterviewTurn.is_followup == False)
        .order_by(InterviewTurn.turn_index.desc())
    ).first()


class AgenticInterviewAgent:
    """
    True agentic interview orchestrator with reasoning loop.

    Uses:
    - Gemini function calling for tool use
    - Think-act-observe loop for autonomous decision making
    - Agent context for memory and state
    """

    def __init__(self):
        self.reasoning_loop = AgentReasoningLoop()


    def _refine_and_translate(self, text: str, type: str, language: str) -> str:
        """Refine and optionally translate the question using LLM."""
        from backend.services.llm_client import call_llm
        
        # If Hebrew, we want strict Hebrew translation + refinement
        if language and language.lower() == "hebrew":
            prompt = f"""Task: Translate and Refine Interview Question.
Target Language: Hebrew (Ivrit).
Instructions:
1. Translate the following technical interview question to professional, natural Hebrew.
2. EXPAND on the question to provide a RICH, DETAILED SCENARIO.
3. Instead of just asking the question, wrap it in a real-world engineering context (e.g., "We are building a financial system...", "We need to parse legacy data...").
4. Make the question feel like a discussion with a senior engineer.
5. Ensure the technical requirements are clear and detailed.
6. Output ONLY the final Hebrew question text (Scenario + Question).

Original Question: "{text}"
Question Type: {type}

Hebrew Question:"""
            try:
                result = call_llm("You are an expert Hebrew technical interviewer.", prompt, prefer="groq")
                if result and result.strip():
                    return result.strip()
            except Exception as e:
                logger.error(f"Refinement/Translation failed: {e}")
                return text # Fallback to original

        # English Refinement
        prompt = f"""Task: Refine Interview Question.
Instructions:
1. Rewrite the following question to include a DETAILED, ENGAGING SCENARIO.
2. Do not just ask the question. Set the scene. (e.g., "Imagine we are processing large log files..." or "We need to optimize a critical path...").
3. Make it sound like a peer-to-peer engineering discussion.
4. Ensure the core technical question is preserved but framed naturally.
5. Output ONLY the refined question text.

Original Question: "{text}"
Question Type: {type}

Refined Question:"""
        try:
            result = call_llm("You are an expert technical interviewer.", prompt, prefer="groq")
            if result and result.strip():
                return result.strip()
        except Exception as e:
            logger.error(f"Refinement failed: {e}")
        
        return text

    def process_turn(
        self,
        request: InterviewNextRequest,
        interview_session: InterviewSession,
        plan_items: List[Dict[str, Any]],
        role_profile: Dict[str, Any],
        session: Session,
    ) -> Dict[str, Any]:
        """Process a turn using the agentic reasoning loop."""
        state = _load_state(interview_session)
        followup_count = state["followup_count"]
        question_index = state["question_index"]
        previous_followups = state["previous_followups"]

        # Check if interview is complete
        if followup_count == 0 and question_index >= len(plan_items):
            interview_session.ended_at = datetime.utcnow()
            session.add(interview_session)
            session.commit()
            return {
                "interviewer_message": "Thank you! The interview is complete.",
                "followup_question": None,
                "next_question": None,
                "is_done": True,
                "progress": {"turn_index": question_index, "total": len(plan_items)},
            }

        # Get current question
        plan_item = plan_items[question_index] if question_index < len(plan_items) else {}
        question_id = state.get("current_question_id") if followup_count > 0 else plan_item.get("selected_question_id")

        question = session.get(QuestionBank, question_id)
        if not question:
            return self._error_response(question_index, len(plan_items))

        # --- REFINEMENT CHECK ---
        # Check if we have a refined version of this question in state
        refined_key = f"refined_q_{question_index}"
        
        # SAFETY: Detach 'question' from session before modifying text
        # This prevents the refined/translated text from overwriting the original in the database
        session.expunge(question)

        if refined_key in state:
            # Use the pre-calculated refined text for the Agent's context
            question.question_text = state[refined_key]
        else:
            # If not in state (e.g. first run or legacy), try to refine now
            # Get language directly from session
            lang = interview_session.language if interview_session.language else "english"
            
            # Refine/Translate
            refined_text = self._refine_and_translate(question.question_text, plan_item.get("type", "open"), lang)
            
            # Updates
            state[refined_key] = refined_text
            question.question_text = refined_text
            
            # We need to save this state update
            _save_state(interview_session, state, session)
        # ------------------------

        # Build agent context
        # Get persona from interview session (defaults to "friendly")
        persona = getattr(interview_session, "persona", "friendly")
        # Get language (defaults to "english")
        language = interview_session.language if interview_session.language else "english"
        logger.error(f"[AGENT] Session Language: {language}")
        
        context = build_context_from_request(
            session_id=request.session_id,
            question=question,
            request=request,
            plan_items=plan_items,
            role_profile=role_profile,
            state=state,
            persona=persona,
            language=language
        )

        # Run the reasoning loop
        try:
            decision = self.reasoning_loop.run(context)
        except Exception as e:
            logger.error(f"Agent reasoning failed: {e}")
            # Fallback to advancing on error
            decision = AgentDecision(
                action="advance",
                message="Let's continue with the next question.",
                satisfaction_score=0.5,
                reasoning_trace=[]
            )

        # Record the turn
        turn = self._create_turn(
            request=request,
            question=question,
            question_index=question_index,
            followup_count=followup_count,
            decision=decision,
            session=session,
        )
        session.add(turn)
        session.commit()

        # Process the decision
        return self._process_decision(
            decision=decision,
            question=question,
            question_id=question_id,
            question_index=question_index,
            followup_count=followup_count,
            previous_followups=previous_followups,
            plan_items=plan_items,
            interview_session=interview_session,
            state=state,
            session=session,
            language=language,
        )

    def _process_decision(
        self,
        decision: AgentDecision,
        question: QuestionBank,
        question_id: str,
        question_index: int,
        followup_count: int,
        previous_followups: List[str],
        plan_items: List[Dict[str, Any]],
        interview_session: InterviewSession,
        state: Dict[str, Any],
        session: Session,
        language: str = "english",
    ) -> Dict[str, Any]:
        """Process the agent's decision and return API response."""

        if decision.action == "followup" and decision.followup_question:
            # Agent wants to ask a follow-up
            state["current_question_id"] = question_id
            state["followup_count"] = followup_count + 1
            state["initial_answer_score"] = decision.satisfaction_score
            state["previous_followups"] = previous_followups + [decision.followup_question]
            _save_state(interview_session, state, session)

            # Use agent's natural response - if empty, just use the followup directly
            if decision.message:
                message = decision.message
            else:
                # Agent didn't generate natural response - use followup question directly
                message = decision.followup_question

            return {
                "interviewer_message": message,
                "followup_question": {"text": decision.followup_question},
                "next_question": None,
                "is_done": False,
                "progress": {"turn_index": question_index + 1, "total": len(plan_items)},
                "agent_decision": decision.action,
                "agent_confidence": decision.satisfaction_score,
            }

        if decision.action == "hint":
            # Agent is giving a hint (stay on same question)
            # Use agent's message directly - it should contain natural response + hint
            return {
                "interviewer_message": decision.message or "Let me give you a hint.",
                "followup_question": None,
                "next_question": None,
                "is_done": False,
                "progress": {"turn_index": question_index + 1, "total": len(plan_items)},
                "agent_decision": decision.action,
            }

        if decision.action == "end":
            # Agent is ending the interview
            interview_session.ended_at = datetime.utcnow()
            session.add(interview_session)
            session.commit()
            return {
                "interviewer_message": decision.message or "Thank you for your time today.",
                "followup_question": None,
                "next_question": None,
                "is_done": True,
                "progress": {"turn_index": question_index + 1, "total": len(plan_items)},
                "agent_decision": decision.action,
            }

        # Default: advance to next question
        state["question_index"] = question_index + 1
        state["followup_count"] = 0
        state["previous_followups"] = []
        _save_state(interview_session, state, session)

        next_question_data = self._get_next_question_data(
            question_index + 1, plan_items, session, language, interview_session, state
        )

        interview_session.question_start_time = datetime.utcnow()
        session.add(interview_session)
        session.commit()

        # Build the message: use agent's natural response
        if decision.message:
            # Agent generated a natural transition
            message = decision.message
        else:
            # Agent didn't generate transition - provide the next question directly
            if next_question_data:
                message = "בוא נמשיך לשאלה הבאה." if language.lower() == "hebrew" else "Let's move to the next question."
            else:
                message = "מצוין! בוא נמשיך." if language.lower() == "hebrew" else "Great! Let's continue."
                
        return {
            "interviewer_message": message,
            "followup_question": None,
            "next_question": next_question_data,
            "is_done": question_index + 1 >= len(plan_items),
            "progress": {"turn_index": question_index + 1, "total": len(plan_items)},
            "agent_decision": decision.action,
            "agent_confidence": decision.satisfaction_score,
        }

    def _create_turn(
        self,
        request: InterviewNextRequest,
        question: QuestionBank,
        question_index: int,
        followup_count: int,
        decision: AgentDecision,
        session: Session,
    ) -> InterviewTurn:
        """Create an InterviewTurn record."""
        topics = json.loads(question.topics_json or "[]")

        turn = InterviewTurn(
            id=str(uuid.uuid4()),
            session_id=request.session_id,
            turn_index=len(session.exec(
                select(InterviewTurn).where(InterviewTurn.session_id == request.session_id)
            ).all()),
            question_id=question.id,
            question_snapshot=question.question_text,
            user_transcript=request.user_transcript,
            user_code=request.user_code,
            score_json=json.dumps({"overall": decision.satisfaction_score}),
            topics_json=json.dumps(topics),
            parent_turn_id=None,
            question_number=question_index,
            is_followup=followup_count > 0,
            time_spent_seconds=getattr(request, "elapsed_seconds", 0) or 0,
            agent_analysis_json=json.dumps(decision.to_dict()),
        )

        if followup_count > 0:
            parent_turn = _get_last_main_turn(request.session_id, session)
            if parent_turn:
                turn.parent_turn_id = parent_turn.id

        return turn

    def _get_next_question_data(
        self,
        next_index: int,
        plan_items: List[Dict[str, Any]],
        session: Session,
        language: str = "english",
        interview_session: Optional[InterviewSession] = None,
        state: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Get the next question data if available."""
        if next_index >= len(plan_items):
            return None

        next_item = plan_items[next_index]
        next_question_id = next_item.get("selected_question_id")
        next_question = session.get(QuestionBank, next_question_id)

        if next_question:
            question_text = next_question.question_text
            
            # Helper to save state if we refine content
            refined_key = f"refined_q_{next_index}"
            
            # Check if we already refined it (if state provided)
            if state and refined_key in state:
                question_text = state[refined_key]
            else:
                # Refine/Translate now
                question_text = self._refine_and_translate(
                    next_question.question_text, 
                    next_item.get("type", "open"), 
                    language
                )
                
                # Save to state if possible so we don't re-run or lose consistency
                if state is not None and interview_session:
                    state[refined_key] = question_text
                    # We utilize the helper _save_state but we need to ensure we don't conflict 
                    # with other saves. Since this is usually called from process_decision which just saved,
                    # we do another save.
                    try:
                        _save_state(interview_session, state, session)
                    except Exception as e:
                        logger.error(f"Failed to save refined question state: {e}")

            return {
                "question_id": next_question.id,
                "text": question_text,
                "type": next_item.get("type", "open"),
                "topics": json.loads(next_question.topics_json or "[]"),
            }
        return None

    def _error_response(self, question_index: int, total: int) -> Dict[str, Any]:
        """Return an error response."""
        return {
            "interviewer_message": "Sorry, I hit an error loading the question.",
            "followup_question": None,
            "next_question": None,
            "is_done": True,
            "progress": {"turn_index": question_index, "total": total},
        }


# =============================================================================
# Legacy Implementation (State Machine)
# =============================================================================

class InterviewAgent:
    """
    Interview agent using true agentic flow with reasoning loop and tool use.
    """

    def __init__(self):
        self._agentic = AgenticInterviewAgent()

    def process_turn(
        self,
        request: InterviewNextRequest,
        interview_session: InterviewSession,
        plan_items: List[Dict[str, Any]],
        role_profile: Dict[str, Any],
        session: Session,
    ) -> Dict[str, Any]:
        """Process a turn using agentic flow."""
        logger.info("Using agentic interview flow")
        return self._agentic.process_turn(
            request, interview_session, plan_items, role_profile, session
        )


