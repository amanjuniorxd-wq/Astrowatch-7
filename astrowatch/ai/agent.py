"""
Astrowatch Online -- autonomous agent (task spec Section 21).
=================================================================
The 11-step flow, each step backed by a real, already-built piece of this
project (no new calculation logic lives here -- this module is pure
orchestration):

    1. Discover potential prediction topics    -> random_prediction.select_candidate()
    2. Select a suitable candidate              -> (same call, weighted-random pick)
    3. Identify entities                        -> selection["entity"] (a real entities_db row)
    4. Verify entity data                       -> entities_db row already has real date/place/source
    5. Determine time horizon                   -> selection["horizon_days"]
    6. Run Astrowatch                           -> tools.calculate_entity_chart (inside prediction_agent)
    7. Run applicable astrology engines          -> tools.run_jyotisha_prediction /
                                                    run_cross_tradition_analysis / run_world_astrology
    8. Compare results                          -> classify_agreement() (inside run_cross_tradition_analysis)
    9. Generate final prediction                -> ai.synthesis.build_final_result()
    10. Save it                                 -> predictions_db (skipped if dry_run)
    11. Return it                               -> the return value of run()
"""

from typing import Any, Dict, Optional

from . import random_prediction


def run(dry_run: bool = False, category: Optional[str] = None,
        mode: str = "detailed") -> Dict[str, Any]:
    """dry_run=True runs the full real pipeline (steps 1-9 above, including
    any configured OpenAI synthesis) but skips step 10 (persistence) -- for
    testing the agent without adding to prediction history or affecting
    future novelty scoring. Never fakes or skips the calculation/synthesis
    steps themselves."""
    result = random_prediction.generate_random_prediction(
        category=category, mode=mode, persist=not dry_run,
    )
    result["agent_run"] = True
    result["dry_run"] = dry_run
    return result
