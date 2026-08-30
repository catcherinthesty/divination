"""Markdown renderer for Gematria reports."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..renderer.chart_writer import atomic_write
from .calculations import compute_all
from .data_types import GematriaRecord, System
from .interpretations import get_core_interpretation, get_famous_pairs


def render_markdown(
    record: GematriaRecord,
    initials: str,
    output_dir: str | Path = ".",
) -> str:
    """Generate a Markdown gematria report.

    Returns the path to the written file as a string.
    """
    result = compute_all(record)
    out = Path(output_dir)

    systems_order = [System.SIMPLE, System.ORDINAL, System.REVERSE]
    system_labels = {
        System.SIMPLE: "Simple (Pythagorean)",
        System.ORDINAL: "Full Ordinal",
        System.REVERSE: "Reverse Ordinal",
    }

    # Build report sections
    sections: list[str] = []

    # Title
    sections.append(f"# Gematria Report: {result.name}")
    sections.append("")

    # Overview table
    sections.append("## Overview")
    sections.append("")
    sections.append("| System | Total | Reduced | Initials Value |")
    sections.append("|--------|-------|---------|----------------|")

    for sys_obj in systems_order:
        if sys_obj not in result.results:
            continue
        sr = result.results[sys_obj]
        label = system_labels.get(sys_obj, sys_obj.value)
        sections.append(f"| {label} | {sr.total} | **{sr.reduced}** | {sr.initials_value} |")

    sections.append("")

    # Detailed results per system
    for sys_obj in systems_order:
        if sys_obj not in result.results:
            continue
        sr = result.results[sys_obj]
        label = system_labels.get(sys_obj, sys_obj.value)

        sections.append(f"## {label}")
        sections.append("")
        sections.append(f"**Total:** {sr.total}  ")
        sections.append(f"**Reduced:** {sr.reduced}")
        sections.append("")

        # Interpretation
        interp = get_core_interpretation(sr.reduced)
        sections.append(f"### Interpretation: {interp.get('title', '')}")
        sections.append("")
        sections.append(f"{interp.get('summary', '')}")
        sections.append("")

        strengths = interp.get("strengths", [])
        challenges = interp.get("challenges", [])
        if strengths:
            sections.append(f"**Strengths:** {', '.join(str(s) for s in strengths)}")
            sections.append("")
        if challenges:
            sections.append(f"**Challenges:** {', '.join(str(c) for c in challenges)}")
            sections.append("")

        # Famous pairs
        famous = get_famous_pairs(sr.reduced)
        if famous:
            sections.append("**Famous Pairs:**")
            sections.append("")
            for val, desc in famous[:8]:
                sections.append(f"- {val}: {desc}")
            sections.append("")

        # Word breakdown table
        sections.append("### Word Breakdown")
        sections.append("")
        sections.append("| Word | Total | Reduced | Vowels | Consonants |")
        sections.append("|------|-------|---------|--------|------------|")

        for wd in sr.words:
            sections.append(
                f"| {wd.word} | {wd.total} | {wd.reduced} | {wd.vowel_total} | {wd.consonant_total} |"
            )

        sections.append("")

    # Summary
    sections.append("## Summary")
    sections.append("")
    sections.append(f"**Name:** {result.name}")
    sections.append(f"**Initials:** {result.initials}")
    sections.append(f"**Systems Computed:** {len(result.results)}")
    sections.append("")

    content = "\n".join(sections) + "\n"
    path = out / f"{initials}_gematria.md"
    atomic_write(str(path), content)
    return str(path)
