"""
GuardianVerificationEngine.py

Handles verification of @During and @Post intent annotations.
Provides temporal state checking capabilities for SolQDebug.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Dict, Any, List, Optional

if TYPE_CHECKING:
    from Analyzer.ContractAnalyzer import ContractAnalyzer

from Domain.Variable import Variables
from Domain.Interval import IntegerInterval, UnsignedIntegerInterval, BoolInterval
from Domain.IR import Expression
from Utils.Helper import VariableEnv
from Utils.CFG import CFGNode


class GuardianVerificationEngine:
    def __init__(self, analyzer: "ContractAnalyzer"):
        self.analyzer = analyzer

    # === DURING =====================================================

    # === DURING =====================================================
    def verify_during_before_after(
        self, *, var_ref: Expression, comp_op: str,
        line_no: int, cfg_node: CFGNode
    ) -> dict[str, any]:

        try:
            # 1. before / after variable environments -----------------
            before_env = cfg_node.before_envs.get(line_no)
            if before_env is None:
                return self._err(
                    "duringBeforeAfter",
                    f"no before-env captured for line {line_no}", line_no
                )

            after_env  = cfg_node.variables

            # 2. evaluate var_ref in the two envs ---------------------
            ev = self.analyzer.evaluator   # shorthand
            before_val = ev.evaluate_expression(var_ref, before_env, None, None)
            after_val  = ev.evaluate_expression(var_ref, after_env,  None, None)

            # 3. compare ---------------------------------------------
            cmp_res = ev.compare_intervals(before_val, after_val, comp_op)
            status  = "success" if cmp_res["satisfied"] else "violation"

            return {
                "status":  status,
                "kind":    "duringBeforeAfter",
                "line":    line_no,
                "details": {
                    "variable":    self._pretty_expr(var_ref),
                    "before":      str(before_val),
                    "after":       str(after_val),
                    "operator":    comp_op,
                    "satisfied":   cmp_res["satisfied"],
                },
                "message": f'{self._pretty_expr(var_ref)}(Before {comp_op} After) '
                           f'→ {cmp_res["message"]}',
            }

        except Exception as e:
            return self._err("duringBeforeAfter", f"internal error: {e}", line_no)

    def verify_during_assign_current(self, *, var_ref, comp_op, line_no, cfg_node):
        return self._todo("duringAssignCurrent", line_no)

    def verify_during_return_expression(self, *, comp_op, value_expr, line_no, cfg_node):
        return self._todo("duringRetExpr", line_no)

    def verify_during_return_variable(self, *, var_ref, comp_op, value_expr, line_no, cfg_node):
        return self._todo("duringRetVar", line_no)

    def verify_during_direct_comparison(self, *, lhs_expr, comp_op, rhs_expr, line_no, cfg_node):
        return self._todo("duringDirectCmp", line_no)

    # === POST =======================================================

    def verify_post_entry_exit(self, *, var_ref, comp_op, line_no, fn_cfg):
        return self._todo("postEntryExit", line_no)

    def verify_post_return_expression(self, *, comp_op, value_expr, line_no, fn_cfg):
        return self._todo("postRetExpr", line_no)

    def verify_post_return_variable(self, *, var_ref, comp_op, value_expr, line_no, fn_cfg):
        return self._todo("postRetVar", line_no)

    def verify_post_direct_comparison(self, *, lhs_expr, comp_op, rhs_expr, line_no, fn_cfg):
        return self._todo("postDirectCmp", line_no)

    def verify_post_unchanged(self, *, var_ref, line_no, fn_cfg):
        return self._todo("postUnchanged", line_no)

    # ---------------------------------------------------------------
    # Simple placeholders
    # ---------------------------------------------------------------
    def _ok(self, tag, ln):
        return {"status": "success", "message": f"{tag} satisfied (stub)", "line": ln}

    def _todo(self, tag, ln):
        return {"status": "todo", "message": f"{tag} verification not implemented yet", "line": ln}

    # ----------------------------------------------------------------
    # helper: uniform ok / error payloads
    # ----------------------------------------------------------------
    def _err(self, kind: str, msg: str, ln: int) -> dict[str, any]:
        return {"status": "error", "kind": kind, "line": ln, "message": msg}

    def _pretty_expr(self, expr: Expression) -> str:
        """very small utility – turn Expression into a readable string"""
        return getattr(expr, "identifier", "") or str(expr)

    # ----------------------------------------------------------------
    # Interval-aware comparison with probability
    # ----------------------------------------------------------------
    def _compare_intervals_prob(self, left_iv, right_iv, op: str) -> dict:
        """
        두 Interval 사이의 관계를
          - 'satisfied' : 반드시 성립
          - 'violated'  : 절대 성립 불가
          - 'uncertain' : 일부 구간만 성립
        로 판정하고, uncertain 인 경우에는
          confidence ∈ (0,1)  ≒  '성립할 확률' 값을 계산한다.
        """

        # ③ op 별 true-zone, false-zone 계산 --------------------------
        def _overlap(a1, a2, b1, b2):
            """두 구간 [a1,a2], [b1,b2] 의 겹치는 길이"""
            return max(0, min(a2, b2) - max(a1, b1))

        # ① min/max 가 None → 정보 부족 → 완전 불확정
        if (left_iv.min_value is None or left_iv.max_value is None or
                right_iv.min_value is None or right_iv.max_value is None):
            return {"state": "uncertain", "confidence": 0.5}

        # ② Interval 폭
        lw, rw = left_iv.max_value - left_iv.min_value, right_iv.max_value - right_iv.min_value

        # ─── 포함(in) / 비포함(not in) ────────────────────────────
        if op in {"in", "not in"}:
            # left ⊆ right ?   (구간 포함 여부)
            left_inside = (left_iv.min_value >= right_iv.min_value and
                           left_iv.max_value <= right_iv.max_value)
            if left_inside:
                return {"state": "satisfied" if op == "in" else "violated",
                        "confidence": 1.0}
            # 완전히 분리 → ‘in’ 은 false 확정,  ‘not in’ 은 true 확정
            separated = (left_iv.max_value < right_iv.min_value or
                         left_iv.min_value > right_iv.max_value)
            if separated:
                return {"state": "violated" if op == "in" else "satisfied",
                        "confidence": 1.0}
            # 부분-겹침 → 불확정, 겹치는 비율을 신뢰도로
            overlap = max(0, min(left_iv.max_value, right_iv.max_value) -
                          max(left_iv.min_value, right_iv.min_value))
            conf = 1 - overlap / lw if op == "not in" else overlap / lw
            return {"state": "uncertain", "confidence": round(conf, 3)}

        if op == '>':
            true_len = max(0, left_iv.max_value - max(left_iv.min_value, right_iv.max_value))
            false_len = max(0, min(left_iv.max_value, right_iv.min_value) - left_iv.min_value)
            total = lw
        elif op == '<':
            true_len = max(0, min(left_iv.max_value, right_iv.min_value) - left_iv.min_value)
            false_len = max(0, right_iv.max_value - max(right_iv.min_value, left_iv.max_value))
            total = lw
        elif op == '>=':
            true_len = max(0, left_iv.max_value - right_iv.min_value + 1)
            false_len = max(0, right_iv.max_value - left_iv.max_value - 1)
            total = lw + 1  # 보수적인 처리
        elif op == '<=':
            true_len = max(0, right_iv.max_value - left_iv.min_value + 1)
            false_len = max(0, left_iv.min_value - right_iv.min_value - 1)
            total = lw + 1
        elif op == '==':
            # 겹치는 길이를 “true”, 나머지를 “false”
            true_len = _overlap(left_iv.min_value, left_iv.max_value,
                                right_iv.min_value, right_iv.max_value)
            false_len = lw - true_len
            total = lw
        elif op == '!=':
            true_len = lw - _overlap(left_iv.min_value, left_iv.max_value,
                                     right_iv.min_value, right_iv.max_value)
            false_len = lw - true_len
            total = lw
        else:
            raise ValueError(f"unsupported op {op}")

        # ④ 결과 state / confidence ----------------------------------
        if false_len == 0:
            return {"state": "satisfied", "confidence": 1.0}
        if true_len == 0:
            return {"state": "violated", "confidence": 0.0}

        conf = true_len / total if total else 0.5
        return {"state": "uncertain", "confidence": round(conf, 3)}

    def _compare_values(self, left, op: str, right) -> dict:
        """
        Interval  ➜  확률 기반 판정
        스칼라    ➜  기존 True/False
        """
        # Interval ↔ Interval ----------------------------------------
        if (hasattr(left, "min_value") and hasattr(right, "min_value")):
            info = self._compare_intervals_prob(left, right, op)
            return {
                "satisfied": info["state"] == "satisfied",
                "violated": info["state"] == "violated",
                "uncertain": info["state"] == "uncertain",
                "confidence": info["confidence"],
                "message": f"{info['state']} (conf={info['confidence']})"
            }

        # 스칼라 ↔ 스칼라 --------------------------------------------
        try:
            tbl = {
                '<': lambda a, b: a < b,
                '>': lambda a, b: a > b,
                '<=': lambda a, b: a <= b,
                '>=': lambda a, b: a >= b,
                '==': lambda a, b: a == b,
                '!=': lambda a, b: a != b,
            }
            satisfied = tbl[op](left, right)
            return {
                "satisfied": satisfied,
                "violated": not satisfied,
                "uncertain": False,
                "confidence": 1.0,
                "message": f"{left} {op} {right} = {satisfied}"
            }
        except Exception as e:
            return {"satisfied": False, "violated": True,
                    "uncertain": True, "confidence": 0.0,
                    "message": f"comparison error: {e}"}
