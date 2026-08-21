from __future__ import annotations

from datetime import timedelta
from statistics import mean
from typing import Any

from celery import chain, chord, group, shared_task
from django.conf import settings
from django.utils import timezone

from agents.adversarial.graph import build_adversarial_agent_graph
from agents.base.checkpointer import get_checkpointer
from agents.base.registry import AgentRegistry, register_default_agents
from agents.pm.graph import build_pm_agent_graph
from apps.audit.models import AuditAction
from apps.audit.services import AuditService
from apps.core.domain.enums import PipelineStatus
from apps.market_data.models import OHLCVBar
from apps.orchestrator.repositories import AnalysisRunRepository
from apps.orchestrator.services import (
    AgentInputBuilder,
    ApprovalChain,
    PipelineStepService,
)
from apps.portfolio.models import ExitPackageStatus, PMReviewRequest
from apps.portfolio.services import PortfolioService
from apps.research.models import BullBearDecisionMemo, PeerAnalysisReport, SpecialistReport
from apps.risk_compliance.services import ComplianceService, RiskService
from apps.signals.models import ConvictionScorePackage, SignalAgreementMatrix
from apps.signals.services import SignalExtractionService
from engines.peer.relative_value_engine import RelativeValueEngine
from rules.conviction.conviction_rules import ConvictionRules
from rules.conviction.signal_aggregator import SignalAggregator

repository = AnalysisRunRepository()
steps = PipelineStepService()
inputs = AgentInputBuilder()


def build_analysis_canvas(run_id: str):
    """Build the plan-mandated outer Celery pipeline."""

    return chain(
        validate_canonical_data.si(run_id),
        chord(
            group(
                extract_signal_domain.si(run_id, domain)
                for domain in (
                    "technical",
                    "fundamental",
                    "macro",
                    "sentiment",
                )
            ),
            signals_completed.si(run_id),
        ),
        chord(
            group(
                run_specialist_agent.si(run_id, agent_id)
                for agent_id in (
                    "macro",
                    "fundamental",
                    "technical",
                    "sentiment",
                )
            ),
            specialists_completed.si(run_id),
        ),
        run_peer_analysis.si(run_id),
        run_adversarial_review.si(run_id),
        run_conviction_scoring.si(run_id),
        run_risk_validation.si(run_id),
        run_compliance_check.si(run_id),
        run_position_sizing.si(run_id),
        run_portfolio_optimization.si(run_id),
        run_pm_synthesis.si(run_id),
    )


def _fail(run_id: str, exc: Exception) -> None:
    repository.get(run_id).fail(str(exc))


@shared_task(name="apps.orchestrator.tasks.validate_canonical_data")
def validate_canonical_data(run_id: str) -> dict[str, Any]:
    run = repository.get(run_id)
    try:
        run.transition_to(PipelineStatus.INGESTING)
        with steps.track(run, name="ingestion_and_normalization", sequence=1) as output:
            output.update(
                {
                    "ohlcv_records": OHLCVBar.objects.filter(
                        ticker=run.ticker,
                        timestamp__lte=run.data_cutoff_at,
                        available_at__lte=run.data_cutoff_at,
                    ).count(),
                    "financial_statements": run.ticker.financial_statements.filter(
                        available_at__lte=run.data_cutoff_at,
                    ).count(),
                    "news_items": run.ticker.news_items.filter(
                        published_at__lte=run.data_cutoff_at,
                        available_at__lte=run.data_cutoff_at,
                    ).count(),
                    "mode": "canonical_store_validation",
                }
            )
        run.transition_to(PipelineStatus.EXTRACTING_SIGNALS)
        return output
    except Exception as exc:
        _fail(run_id, exc)
        raise


@shared_task(name="apps.orchestrator.tasks.extract_signal_domain")
def extract_signal_domain(run_id: str, domain: str) -> dict[str, Any]:
    run = repository.get(run_id)
    try:
        with steps.track(run, name=f"signal_{domain}", sequence=2) as output:
            if domain == "technical":
                output.update(
                    SignalExtractionService().extract_technical(
                        run.ticker,
                        as_of=run.data_cutoff_at,
                    )
                )
            else:
                output.update(run.analysis_config.get("signal_inputs", {}).get(domain, {}))
                output.setdefault("status", "available_to_agent")
        return output
    except Exception as exc:
        _fail(run_id, exc)
        raise


@shared_task(name="apps.orchestrator.tasks.signals_completed")
def signals_completed(run_id: str) -> dict[str, str]:
    run = repository.get(run_id)
    run.transition_to(PipelineStatus.RUNNING_SPECIALISTS)
    return {"status": run.status}


@shared_task(name="apps.orchestrator.tasks.run_specialist_agent", bind=True, max_retries=2)
def run_specialist_agent(self, run_id: str, agent_id: str) -> dict[str, Any]:
    run = repository.get(run_id)
    try:
        register_default_agents()
        agent_input = inputs.build(run, agent_id)
        with steps.track(
            run,
            name=f"agent_{agent_id}",
            sequence=3,
            attempt=self.request.retries + 1,
            input_snapshot=agent_input,
            task_id=self.request.id or "",
        ) as snapshot:
            with get_checkpointer() as checkpointer:
                graph = AgentRegistry.create(
                    agent_id,
                    checkpointer=checkpointer,
                )
                result = graph.invoke(
                    {
                        "messages": [],
                        "analysis_run_id": str(run.id),
                        "ticker": run.ticker.symbol,
                        "input_data": agent_input,
                        "trace": [],
                    },
                    config={
                        "configurable": {
                            "thread_id": f"{run.checkpoint_thread_id}-{agent_id}",
                        }
                    },
                )
            output = result["agent_output"]
            metadata = output.get("metadata", {})
            SpecialistReport.objects.update_or_create(
                analysis_run_id=run.id,
                specialist_type=agent_id,
                version=1,
                defaults={
                    "run": run,
                    "ticker": run.ticker,
                    "thesis": output.get("thesis", output["summary"]),
                    "summary": output["summary"],
                    "evidence": output.get("evidence", []),
                    "assumptions": output.get("assumptions", []),
                    "limitations": output.get("limitations", []),
                    "confidence": output["confidence"],
                    "stance": output.get("stance", output.get("equity_impact", "neutral")),
                    "input_references": list(agent_input),
                    "output_snapshot": output,
                    "generated_at": timezone.now(),
                    "agent_version": metadata.get("agent_version", ""),
                    "model_version": metadata.get("model_name", ""),
                    "prompt_version": metadata.get("prompt_version", ""),
                },
            )
            snapshot.update(output)
        return output
    except Exception as exc:
        if self.request.retries >= self.max_retries:
            _fail(run_id, exc)
        raise self.retry(exc=exc, countdown=2**self.request.retries) from exc


@shared_task(name="apps.orchestrator.tasks.specialists_completed")
def specialists_completed(run_id: str) -> dict[str, str]:
    run = repository.get(run_id)
    run.transition_to(PipelineStatus.PEER_ANALYSIS)
    return {"status": run.status}


@shared_task(name="apps.orchestrator.tasks.run_peer_analysis")
def run_peer_analysis(run_id: str) -> dict[str, Any]:
    run = repository.get(run_id)
    try:
        peer_inputs = run.analysis_config.get("peer_inputs")
        with steps.track(run, name="peer_analysis", sequence=4) as snapshot:
            result = (
                RelativeValueEngine().compute(peer_inputs)
                if peer_inputs
                else {
                    "target": run.ticker.symbol,
                    "ranking": [],
                    "rationale": "No configured peer dataset was available.",
                }
            )
            PeerAnalysisReport.objects.update_or_create(
                analysis_run_id=run.id,
                version=1,
                defaults={
                    "run": run,
                    "ticker": run.ticker,
                    "comparison_dimensions": peer_inputs or {},
                    "relative_ranking": result.get("ranking", []),
                    "differentiators": [],
                    "summary": result["rationale"],
                    "evidence": [],
                },
            )
            snapshot.update(result)
        run.transition_to(PipelineStatus.ADVERSARIAL_REVIEW)
        return result
    except Exception as exc:
        _fail(run_id, exc)
        raise


@shared_task(name="apps.orchestrator.tasks.run_adversarial_review", bind=True, max_retries=2)
def run_adversarial_review(self, run_id: str) -> dict[str, Any]:
    run = repository.get(run_id)
    try:
        reports = {
            report.specialist_type: report.output_snapshot
            for report in SpecialistReport.objects.filter(run=run)
        }
        with steps.track(
            run,
            name="adversarial_review",
            sequence=5,
            attempt=self.request.retries + 1,
        ) as snapshot:
            with get_checkpointer() as checkpointer:
                graph = build_adversarial_agent_graph(checkpointer=checkpointer)
                result = graph.invoke(
                    {
                        "messages": [],
                        "analysis_run_id": str(run.id),
                        "ticker": run.ticker.symbol,
                        "specialist_outputs": reports,
                        "input_data": run.analysis_config.get("agent_inputs", {}).get(
                            "adversarial",
                            {},
                        ),
                        "debate_round": 0,
                        "bull_arguments": [],
                        "bear_arguments": [],
                        "trace": [],
                    },
                    config={
                        "configurable": {
                            "thread_id": f"{run.checkpoint_thread_id}-adversarial",
                        }
                    },
                )
            output = result["agent_output"]
            metadata = output.get("metadata", {})
            BullBearDecisionMemo.objects.update_or_create(
                analysis_run_id=run.id,
                version=1,
                defaults={
                    "run": run,
                    "ticker": run.ticker,
                    "bull_case": output["bull_case"],
                    "bear_case": output["bear_case"],
                    "base_case": output["base_case"],
                    "key_disagreements": output.get("contradictions", []),
                    "falsifiers": output.get("invalidating_conditions", []),
                    "evidence": output.get("evidence", []),
                    "confidence": output["confidence"],
                    "weak_assumptions": output.get("weak_assumptions", []),
                    "missing_evidence": output.get("missing_evidence", []),
                    "material_unknowns": output.get("material_unknowns", []),
                    "premortem": output.get("premortem", []),
                    "debate_rounds": result["debate_round"],
                    "output_snapshot": output,
                    "agent_version": metadata.get("agent_version", ""),
                    "model_version": metadata.get("model_name", ""),
                    "prompt_version": metadata.get("prompt_version", ""),
                },
            )
            snapshot.update(output)
        run.transition_to(PipelineStatus.CONVICTION_SCORING)
        return output
    except Exception as exc:
        if self.request.retries >= self.max_retries:
            _fail(run_id, exc)
        raise self.retry(exc=exc, countdown=2**self.request.retries) from exc


@shared_task(name="apps.orchestrator.tasks.run_conviction_scoring")
def run_conviction_scoring(run_id: str) -> dict[str, Any]:
    run = repository.get(run_id)
    try:
        reports = list(SpecialistReport.objects.filter(run=run))
        stances = {report.specialist_type: report.stance or "neutral" for report in reports}
        agreement = SignalAggregator().evaluate({"stances": stances})
        score = mean(report.confidence for report in reports) * 100
        conviction = ConvictionRules().evaluate({"stances": stances, "conviction_score": score})
        with steps.track(run, name="conviction_scoring", sequence=6) as snapshot:
            SignalAgreementMatrix.objects.update_or_create(
                analysis_run_id=run.id,
                version=1,
                defaults={
                    "run": run,
                    "ticker": run.ticker,
                    "signal_stances": agreement["stances"],
                    "agreements": agreement["counts"],
                    "conflicts": agreement["conflicting_agents"],
                    "agreement_ratio": agreement["consensus_degree"],
                },
            )
            ConvictionScorePackage.objects.update_or_create(
                analysis_run_id=run.id,
                version=1,
                defaults={
                    "run": run,
                    "ticker": run.ticker,
                    "score": score,
                    "level": str(conviction["conviction_level"]),
                    "action_signal": conviction["signal"],
                    "expected_return_low": run.analysis_config.get("expected_return_low"),
                    "expected_return_high": run.analysis_config.get("expected_return_high"),
                    "horizon_days": run.analysis_config.get("horizon_days"),
                    "component_scores": {"agreement": agreement, "conviction": conviction},
                    "evidence": [],
                    "caveats": [],
                },
            )
            snapshot.update({"agreement": agreement, "conviction": conviction})
        run.transition_to(PipelineStatus.RISK_VALIDATION)
        return snapshot
    except Exception as exc:
        _fail(run_id, exc)
        raise


@shared_task(name="apps.orchestrator.tasks.run_risk_validation", bind=True, max_retries=2)
def run_risk_validation(self, run_id: str) -> dict[str, Any]:
    run = repository.get(run_id)
    try:
        risk_input = inputs.build(run, "risk")
        with steps.track(
            run,
            name="risk_validation",
            sequence=7,
            attempt=self.request.retries + 1,
        ) as snapshot:
            register_default_agents()
            with get_checkpointer() as checkpointer:
                graph = AgentRegistry.create("risk", checkpointer=checkpointer)
                result = graph.invoke(
                    {
                        "messages": [],
                        "analysis_run_id": str(run.id),
                        "ticker": run.ticker.symbol,
                        "input_data": risk_input,
                        "trace": [],
                    },
                    config={"configurable": {"thread_id": f"{run.checkpoint_thread_id}-risk"}},
                )
            output = result["agent_output"]
            validation = RiskService().validate(
                run,
                metrics=risk_input.get("limit_metrics", {}),
                agent_output=output,
            )
            snapshot.update({"decision": validation.decision, "agent_output": output})
        run.transition_to(PipelineStatus.COMPLIANCE_CHECK)
        return snapshot
    except Exception as exc:
        if self.request.retries >= self.max_retries:
            _fail(run_id, exc)
        raise self.retry(exc=exc, countdown=2**self.request.retries) from exc


@shared_task(name="apps.orchestrator.tasks.run_compliance_check")
def run_compliance_check(run_id: str) -> dict[str, Any]:
    run = repository.get(run_id)
    try:
        context = run.analysis_config.get("compliance_context", {})
        with steps.track(run, name="compliance_check", sequence=8) as snapshot:
            result = ComplianceService().evaluate(run, context)
            gate = ApprovalChain().evaluate(run)
            gate_snapshot = {
                "decision": str(gate.decision),
                "gate": gate.gate,
                "rationale": gate.rationale,
            }
            snapshot.update(
                {
                    "decision": result.decision,
                    "violations": result.violations,
                    "approval_gate": gate_snapshot,
                }
            )
            run.analysis_config = {
                **run.analysis_config,
                "approval_gate": gate_snapshot,
            }
            run.save(update_fields=("analysis_config", "updated_at"))
        if gate.decision == "block":
            run.transition_to(PipelineStatus.BLOCKED)
        else:
            run.transition_to(PipelineStatus.POSITION_SIZING)
        return snapshot
    except Exception as exc:
        _fail(run_id, exc)
        raise


@shared_task(name="apps.orchestrator.tasks.run_position_sizing")
def run_position_sizing(run_id: str) -> dict[str, Any]:
    run = repository.get(run_id)
    try:
        if run.status == PipelineStatus.BLOCKED:
            return steps.skip(
                run,
                name="position_sizing_and_exits",
                sequence=9,
                reason="Binding risk or compliance gate blocked the workflow.",
            )
        latest = (
            OHLCVBar.objects.filter(
                ticker=run.ticker,
                timestamp__lte=run.data_cutoff_at,
                available_at__lte=run.data_cutoff_at,
            )
            .order_by("-timestamp")
            .first()
        )
        price = float(latest.close) if latest else 1.0
        conviction = run.conviction_score.score
        config = {
            "methodology": "fixed_fractional",
            "fraction": 0.02,
            "conviction": conviction,
            "volatility": 0.20,
            "liquidity": 1.0,
            "correlation": 0.0,
            "risk_budget": 1.0,
            "portfolio_value": float(run.analysis_config.get("portfolio_value", 0)),
            "price": price,
            **run.analysis_config.get("sizing_inputs", {}),
        }
        methodology = str(config.pop("methodology"))
        with steps.track(run, name="position_sizing_and_exits", sequence=9) as snapshot:
            gate = run.analysis_config.get("approval_gate", {})
            sizing = (
                PortfolioService().create_no_position_sizing(
                    run,
                    reason=gate.get("rationale", "Binding approval gate."),
                    inputs=config,
                )
                if gate.get("decision") == "block"
                else PortfolioService().create_sizing(
                    run,
                    methodology=methodology,
                    inputs=config,
                )
            )
            exit_inputs = {
                "entry_price": price,
                "stop_loss_pct": 0.08,
                "time_based_review_date": timezone.now() + timedelta(days=30),
                **run.analysis_config.get("exit_inputs", {}),
            }
            exit_package = PortfolioService().create_exit_package(run, inputs=exit_inputs)
            snapshot.update(
                {
                    "sizing_id": str(sizing.id),
                    "exit_package_id": str(exit_package.id),
                }
            )
        run.transition_to(PipelineStatus.PORTFOLIO_OPTIMIZATION)
        return snapshot
    except Exception as exc:
        _fail(run_id, exc)
        raise


@shared_task(name="apps.orchestrator.tasks.run_portfolio_optimization")
def run_portfolio_optimization(run_id: str) -> dict[str, Any]:
    run = repository.get(run_id)
    try:
        if run.status == PipelineStatus.BLOCKED:
            return steps.skip(
                run,
                name="portfolio_optimization",
                sequence=10,
                reason="Binding risk or compliance gate blocked the workflow.",
            )
        config = run.analysis_config.get(
            "optimization_inputs",
            {
                "methodology": "risk_parity",
                "expected_returns": [0.0],
                "covariance_matrix": [[0.04]],
                "constraints": {"assets": [run.ticker.symbol], "maximum_weight": 1.0},
                "current_weights": {run.ticker.symbol: 0.0},
                "portfolio_value": float(run.analysis_config.get("portfolio_value", 0)),
            },
        )
        with steps.track(run, name="portfolio_optimization", sequence=10) as snapshot:
            gate = run.analysis_config.get("approval_gate", {})
            output = (
                PortfolioService().hold_current_allocations(
                    run,
                    inputs=config,
                    reason=gate.get("rationale", "Binding approval gate."),
                )
                if gate.get("decision") == "block"
                else PortfolioService().optimize(run, inputs=config)
            )
            snapshot.update(
                {
                    "target_allocations": output.target_allocations,
                    "rebalance_required": output.rebalance_required,
                }
            )
        run.transition_to(PipelineStatus.PM_SYNTHESIS)
        return snapshot
    except Exception as exc:
        _fail(run_id, exc)
        raise


@shared_task(name="apps.orchestrator.tasks.run_pm_synthesis", bind=True, max_retries=2)
def run_pm_synthesis(self, run_id: str) -> dict[str, Any]:
    run = repository.get(run_id)
    try:
        if run.status == PipelineStatus.BLOCKED:
            return steps.skip(
                run,
                name="pm_synthesis",
                sequence=11,
                reason="Binding risk or compliance gate blocked the workflow.",
            )
        agent_outputs = {
            report.specialist_type: report.output_snapshot
            for report in SpecialistReport.objects.filter(run=run)
        }
        agent_outputs["adversarial"] = run.decision_memo.output_snapshot
        agent_outputs["risk"] = {
            "disposition": run.risk_validation.decision,
            "rationale": run.risk_validation.rationale,
        }
        pm_input = {
            **inputs.build(run, "pm"),
            "agent_outputs": agent_outputs,
            "conviction": {
                "score": run.conviction_score.score,
                "signal": run.conviction_score.action_signal,
            },
            "compliance": {
                "decision": run.compliance_result.decision,
                "violations": run.compliance_result.violations,
            },
            "approval_gate": run.analysis_config.get("approval_gate", {}),
        }
        with steps.track(
            run,
            name="pm_synthesis",
            sequence=11,
            attempt=self.request.retries + 1,
        ) as snapshot:
            with get_checkpointer() as checkpointer:
                graph = build_pm_agent_graph(checkpointer=checkpointer)
                result = graph.invoke(
                    {
                        "messages": [],
                        "analysis_run_id": str(run.id),
                        "ticker": run.ticker.symbol,
                        "input_data": pm_input,
                        "trace": [],
                    },
                    config={"configurable": {"thread_id": f"{run.checkpoint_thread_id}-pm"}},
                )
            draft = result["draft_recommendation"]
            recommendation = PortfolioService().persist_recommendation(run, draft)
            review, _ = PMReviewRequest.objects.update_or_create(
                recommendation=recommendation,
                defaults={
                    "checkpoint_thread_id": f"{run.checkpoint_thread_id}-pm",
                    "expires_at": timezone.now() + timedelta(hours=settings.PM_REVIEW_TTL_HOURS),
                },
            )
            snapshot.update(
                {
                    **draft,
                    "review_request_id": str(review.id),
                    "review_expires_at": review.expires_at.isoformat(),
                }
            )
        run.transition_to(PipelineStatus.AWAITING_PM_APPROVAL)
        return {"status": run.status, "recommendation": draft}
    except Exception as exc:
        if self.request.retries >= self.max_retries:
            _fail(run_id, exc)
        raise self.retry(exc=exc, countdown=2**self.request.retries) from exc


class _ResumeOnlyLLM:
    def with_structured_output(self, schema):
        raise RuntimeError("LLM synthesis must not replay during PM checkpoint resume")


@shared_task(name="apps.orchestrator.tasks.resume_pm_decision")
def resume_pm_decision(
    run_id: str,
    *,
    decision: str,
    rationale: str,
    reviewer_id: str,
) -> dict[str, Any]:
    run = repository.get(run_id)
    try:
        config = {"configurable": {"thread_id": f"{run.checkpoint_thread_id}-pm"}}
        with steps.track(
            run,
            name="pm_human_review_and_finalize",
            sequence=12,
            input_snapshot={"decision": decision, "reviewer_id": reviewer_id},
        ) as snapshot:
            with get_checkpointer() as checkpointer:
                graph = build_pm_agent_graph(
                    llm=_ResumeOnlyLLM(),
                    checkpointer=checkpointer,
                )
                graph.update_state(
                    config,
                    {
                        "human_decision": {
                            "decision": decision,
                            "rationale": rationale,
                            "reviewer_id": reviewer_id,
                        }
                    },
                )
                result = graph.invoke(None, config=config)
            output = result["agent_output"]
            recommendation = PortfolioService().persist_recommendation(run, output)
            recommendation.reviewer_id = reviewer_id
            recommendation.review_rationale = rationale
            recommendation.reviewed_at = timezone.now()
            recommendation.save(
                update_fields=("reviewer", "review_rationale", "reviewed_at", "updated_at")
            )
            if decision == "approve" and hasattr(run, "exit_package"):
                run.exit_package.status = ExitPackageStatus.ACTIVE
                run.exit_package.save(update_fields=("status", "updated_at"))
            snapshot.update(
                {
                    "decision": decision,
                    "recommendation_id": str(recommendation.id),
                }
            )
        with steps.track(
            run,
            name="performance_tracking_initialization",
            sequence=13,
        ) as snapshot:
            snapshot.update(
                {
                    "enabled": decision == "approve",
                    "state": (
                        "awaiting_price_observations"
                        if decision == "approve"
                        else "not_applicable"
                    ),
                }
            )
        run.transition_to(PipelineStatus.COMPLETED)
        AuditService.record_event(
            action=AuditAction.APPROVE if decision == "approve" else AuditAction.REJECT,
            event_type="analysis.pm_review",
            actor=recommendation.reviewer,
            resource_type="PMRecommendation",
            resource_id=str(recommendation.id),
            summary=(
                "Recommendation approved" if decision == "approve" else "Recommendation rejected"
            ),
            metadata={"rationale": rationale},
        )
        return {"status": run.status, "recommendation_id": str(recommendation.id)}
    except Exception as exc:
        _fail(run_id, exc)
        raise
