from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


FIDELITY_ORDER = (
    "exact",
    "retry_recovered",
    "structure_rebuilt",
    "text_only",
    "metadata_only",
    "skipped",
)


@dataclass(frozen=True)
class RecoveryUnit:
    unit_type: str
    unit_name: str
    status: str = "merged"
    fidelity: str = "exact"
    message: str | None = None
    recovery_steps: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class RecoveryInfo:
    status: str = "merged"
    fidelity: str = "exact"
    message: str | None = None
    recovery_steps: tuple[str, ...] = field(default_factory=tuple)
    units: tuple[RecoveryUnit, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class MergeWriteReport:
    output_path: Path
    recoveries: tuple[tuple[str, RecoveryInfo], ...] = field(default_factory=tuple)

    def recovery_map(self) -> dict[str, RecoveryInfo]:
        return {absolute_path: info for absolute_path, info in self.recoveries}


def exact_recovery() -> RecoveryInfo:
    return RecoveryInfo()


def skipped_recovery(*, message: str, recovery_steps: tuple[str, ...] = ()) -> RecoveryInfo:
    return RecoveryInfo(
        status="skipped",
        fidelity="skipped",
        message=message,
        recovery_steps=recovery_steps,
    )


def coerce_write_report(result: Path | MergeWriteReport, sources: list[dict[str, Any]]) -> MergeWriteReport:
    if isinstance(result, MergeWriteReport):
        return result
    return MergeWriteReport(
        output_path=result,
        recoveries=tuple((str(source["absolute_path"]), exact_recovery()) for source in sources),
    )


def recovery_to_dict(info: RecoveryInfo) -> dict[str, Any]:
    return {
        "status": info.status,
        "fidelity": info.fidelity,
        "message": info.message,
        "recovery_steps": list(info.recovery_steps),
        "units": [unit_to_dict(unit) for unit in info.units],
    }


def unit_to_dict(unit: RecoveryUnit) -> dict[str, Any]:
    return {
        "unit_type": unit.unit_type,
        "unit_name": unit.unit_name,
        "status": unit.status,
        "fidelity": unit.fidelity,
        "message": unit.message,
        "recovery_steps": list(unit.recovery_steps),
    }


def recovery_summary(info: RecoveryInfo) -> dict[str, int]:
    rescued_units = sum(1 for unit in info.units if unit.fidelity != "exact" and unit.status == "merged")
    skipped_units = sum(1 for unit in info.units if unit.status == "skipped")
    return {
        "rescued_unit_count": rescued_units,
        "skipped_unit_count": skipped_units,
    }


def combine_recoveries(recoveries: list[RecoveryInfo]) -> RecoveryInfo:
    if not recoveries:
        return exact_recovery()
    status = "merged" if any(info.status == "merged" for info in recoveries) else "skipped"
    merged_fidelities = [info.fidelity for info in recoveries if info.status == "merged" and info.fidelity != "skipped"]
    if status == "merged":
        fidelity = worst_fidelity(merged_fidelities or ["exact"])
    else:
        fidelity = "skipped"
    messages = [info.message for info in recoveries if info.message]
    steps = dedupe_steps(step for info in recoveries for step in info.recovery_steps)
    units = tuple(unit for info in recoveries for unit in info.units)
    return RecoveryInfo(
        status=status,
        fidelity=fidelity,
        message=" / ".join(dict.fromkeys(messages)) or None,
        recovery_steps=steps,
        units=units,
    )


def worst_fidelity(fidelities: Any) -> str:
    order = {name: index for index, name in enumerate(FIDELITY_ORDER)}
    worst = "exact"
    for fidelity in fidelities:
        if order.get(fidelity, 0) >= order[worst]:
            worst = fidelity
    return worst


def dedupe_steps(steps: Any) -> tuple[str, ...]:
    return tuple(dict.fromkeys(step for step in steps if step))


def recovery_totals(recoveries: list[RecoveryInfo]) -> dict[str, int]:
    totals = {
        "rescued_count": 0,
        "rescued_unit_count": 0,
        "skipped_unit_count": 0,
    }
    for info in recoveries:
        if info.fidelity != "exact" and info.status == "merged":
            totals["rescued_count"] += 1
        unit_summary = recovery_summary(info)
        totals["rescued_unit_count"] += unit_summary["rescued_unit_count"]
        totals["skipped_unit_count"] += unit_summary["skipped_unit_count"]
    return totals


def recovery_overview_lines(recoveries: list[RecoveryInfo]) -> list[str]:
    counts: dict[str, int] = {name: 0 for name in FIDELITY_ORDER}
    for info in recoveries:
        counts[info.fidelity] = counts.get(info.fidelity, 0) + 1
    unit_totals = recovery_totals(recoveries)
    return [
        "Recovery summary",
        f"Exact merges: {counts.get('exact', 0)}",
        f"Retry recovered: {counts.get('retry_recovered', 0)}",
        f"Structure rebuilt: {counts.get('structure_rebuilt', 0)}",
        f"Text only: {counts.get('text_only', 0)}",
        f"Metadata only: {counts.get('metadata_only', 0)}",
        f"Skipped sources: {counts.get('skipped', 0)}",
        f"Rescued units: {unit_totals['rescued_unit_count']}",
        f"Skipped units: {unit_totals['skipped_unit_count']}",
    ]


def source_recovery_lines(info: RecoveryInfo) -> list[str]:
    lines = [
        f"Recovery status: {info.status}",
        f"Fidelity: {info.fidelity}",
    ]
    if info.message:
        lines.append(f"Message: {info.message}")
    if info.recovery_steps:
        lines.append(f"Steps: {' -> '.join(info.recovery_steps)}")
    unit_summary = recovery_summary(info)
    if unit_summary["rescued_unit_count"] or unit_summary["skipped_unit_count"]:
        lines.append(f"Rescued units: {unit_summary['rescued_unit_count']}")
        lines.append(f"Skipped units: {unit_summary['skipped_unit_count']}")
    return lines
