"""
GuardianVerificationEngine.py

Handles verification of @During and @Post intent annotations.
Provides temporal state checking capabilities for SolQDebug.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from Analyzer.ContractAnalyzer import ContractAnalyzer

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
    ) -> dict[str, Any]:

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

    def verify_during_assign_current(self, *, var_ref, comp_op,
                                     line_no, cfg_node):

        fcfg = self.analyzer.current_target_function_cfg

        # 1)  Assign 값  ― assign_env 를 통째로 변수-환경으로 사용
        assign_val = self.analyzer.evaluator.evaluate_expression(
            var_ref, fcfg.assign_env, None, None)

        if assign_val is None:
            return self._err("duringAssignCurrent",
                             "no initial assignment for variable", line_no)

        # 2)  Current 값
        current_val = self.analyzer.evaluator.evaluate_expression(
            var_ref, cfg_node.variables, None, None)

        # 3)  비교
        cmp = self._compare_values(assign_val, comp_op, current_val)
        status = "success" if cmp["satisfied"] else "violation"

        return {
            "status": status,
            "kind": "duringAssignCurrent",
            "line": line_no,
            "details": {
                "variable": self._expr_to_str(var_ref),
                "assign_value": str(assign_val),
                "current_value": str(current_val),
                "operator": comp_op,
                **cmp
            },
            "message": f'{self._expr_to_str(var_ref)}(Assign {comp_op} Current) '
                       f'→ {cmp["message"]}',
        }

    def verify_during_return_expression(
        self, *, comp_op: str, value_expr: Expression,
        line_no: int, cfg_node: CFGNode
    ) -> dict[str, any]:

        try:
            # ── 1) “현재 함수” CFG -------------------------------
            fcfg = self.analyzer.current_target_function_cfg
            if fcfg is None:
                return self._err("duringRetExpr",
                                  "no active FunctionCFG", line_no)

            # ── 2) return 값 확보 -------------------------------
            # builder 가 EXIT.return_vals[ln] 에 저장해 둔다.
            ret_vals = fcfg.get_exit_node().return_vals
            if line_no not in ret_vals:
                return self._err("duringRetExpr",
                                  f"no return at line {line_no}", line_no)
            ret_val = ret_vals[line_no]

            # ── 3) valueExpr 평가 -------------------------------
            rhs_val = self.analyzer.evaluator.evaluate_expression(
                value_expr, cfg_node.variables, None, None)

            # ── 4) 비교 ----------------------------------------
            cmp = self._compare_values(ret_val, comp_op, rhs_val)
            status = "success" if cmp["satisfied"] else "violation"

            return {
                "status":  status,
                "kind":    "duringRetExpr",
                "line":    line_no,
                "details": {
                    "return_value": str(ret_val),
                    "expected":     str(rhs_val),
                    "operator":     comp_op,
                    **cmp
                },
                "message": (f"returnExpression {comp_op} {self._pretty_expr(value_expr)} "
                            f"→ {cmp['message']}")
            }

        except Exception as e:
            return self._err("duringRetExpr", f"internal error: {e}", line_no)

    # ────────────────────────────────────────────────────────────────
    #  DURING : return var  비교
    # ----------------------------------------------------------------
    def verify_during_return_variable(
            self, *, var_ref, comp_op, value_expr, line_no, cfg_node
    ) -> dict[str, any]:

        try:
            fcfg = self.analyzer.current_target_function_cfg
            exit_n = fcfg.get_exit_node()

            # ① “해당‧또는 가장 가까운 이전” return-값 가져오기 -------------
            if line_no in exit_n.return_vals:
                ret_val = exit_n.return_vals[line_no]
            else:  # 앞쪽에서 찾기
                prevs = [ln for ln in exit_n.return_vals if ln < line_no]
                if not prevs:
                    return self._err("duringRetVar",
                                     "no return value available", line_no)
                ln_sel = max(prevs)  # 가장 가까운 것
                ret_val = exit_n.return_vals[ln_sel]

            # ② LHS 값 추출  -------------------------------------------------
            if var_ref.context == "ReturnElemRef":
                idx = int(var_ref.index.literal, 0)
                if not isinstance(ret_val, (list, tuple)):
                    return self._err("duringRetVar",
                                     "function does not return a tuple", line_no)
                if idx >= len(ret_val):
                    return self._err("duringRetVar",
                                     f"tuple index {idx} out of range", line_no)
                lhs_val = ret_val[idx]

            else:  # 보통의 varRef (이름 있는 return 변수 등)
                lhs_val = self.analyzer.evaluator.evaluate_expression(
                    var_ref, cfg_node.variables, None, None
                )

            # ③ RHS 값 계산  -------------------------------------------------
            rhs_val = self.analyzer.evaluator.evaluate_expression(
                value_expr, cfg_node.variables, None, None
            )

            # ④ 비교  --------------------------------------------------------
            cmp = self._compare_values(lhs_val, comp_op, rhs_val)
            status = "success" if cmp["satisfied"] else "violation"

            return {
                "status": status,
                "kind": "duringRetVar",
                "line": line_no,
                "details": {
                    "variable": self._pretty_expr(var_ref),
                    "actual": str(lhs_val),
                    "expected": str(rhs_val),
                    "operator": comp_op,
                    **cmp
                },
                "message": f'return {self._pretty_expr(var_ref)} {comp_op} '
                           f'{rhs_val}  →  {cmp["message"]}'
            }

        except Exception as e:
            return self._err("duringRetVar", f"internal error: {e}", line_no)

    # ────────────────────────────────────────────────────────────────
    #  DURING :  valueExpr  op  valueExpr
    # ----------------------------------------------------------------
    def verify_during_direct_comparison(
            self, *, lhs_expr, comp_op, rhs_expr, line_no, cfg_node
    ) -> dict[str, any]:

        try:
            ev = self.analyzer.evaluator  # 평가기 단축명
            vars_env = cfg_node.variables  # 현재 변수 Env

            # ① 두 피연산식 계산 -------------------------------------------------
            lhs_val = ev.evaluate_expression(lhs_expr, vars_env, None, None)
            rhs_val = ev.evaluate_expression(rhs_expr, vars_env, None, None)

            # ② 비교 ------------------------------------------------------------
            cmp = self._compare_values(lhs_val, comp_op, rhs_val)
            status = "success" if cmp["satisfied"] else "violation"

            # ③ 결과 dict -------------------------------------------------------
            return {
                "status": status,
                "kind": "duringDirectCmp",
                "line": line_no,
                "details": {
                    "lhs": str(lhs_val),
                    "rhs": str(rhs_val),
                    "operator": comp_op,
                    **cmp  # satisfied / violated / uncertain / confidence
                },
                "message": f'{self._pretty_expr(lhs_expr)} {comp_op} '
                           f'{self._pretty_expr(rhs_expr)}  →  {cmp["message"]}'
            }

        except Exception as e:
            return self._err("duringDirectCmp",
                             f"internal error: {e}", line_no)

    # === POST =======================================================

    # GuardianVerificationEngine.py
    # ────────────────────────────────────────────────────────────────
    #  POST :  varRef( Entry <op> Exit )
    # ----------------------------------------------------------------
    def verify_post_entry_exit(self, *, var_ref, comp_op: str, line_no: int, fn_cfg) -> dict[str, any]:
        ev = self.analyzer.evaluator
        try:
            entry_env = getattr(fn_cfg, "entry_env", fn_cfg.related_variables)
            entry_val = self._materialize(ev.evaluate_expression(var_ref, entry_env, None, None))

            exit_val = self._eval_on_exit_value(var_ref, fn_cfg, normal_only=True)

            cmp = self._compare_values(entry_val, comp_op, exit_val)
            status = "success" if cmp["satisfied"] else "violation"
            return {
                "status": status,
                "kind": "postEntryExit",
                "line": line_no,
                "details": {
                    "variable": self._pretty_expr(var_ref),
                    "entry_value": str(entry_val),
                    "exit_value": str(exit_val),
                    "operator": comp_op,
                    **cmp
                },
                "message": f'{self._pretty_expr(var_ref)}(Entry {comp_op} Exit) → {cmp["message"]}',
            }
        except Exception as e:
            return self._err("postEntryExit", f"internal error: {e}", line_no)

    def verify_post_return_expression(self, *, comp_op: str, value_expr, line_no: int, fn_cfg):
        try:
            exit_node = fn_cfg.get_exit_node()
            ret_vals = list(exit_node.return_vals.values())

            if not ret_vals:
                return_val = None  # void
            else:
                # 값 조인은 list/tuple 가능성 있으니 얇은 어댑터 사용
                acc = ret_vals[0]
                for v in ret_vals[1:]:
                    acc = self._join_values(acc, v)
                return_val = self._materialize(acc)

            rhs_val = self._eval_on_exit_value(value_expr, fn_cfg, normal_only=True)

            cmp = self._compare_values(return_val, comp_op, rhs_val)
            status = "success" if cmp["satisfied"] else "violation"
            return {
                "status": status,
                "kind": "postRetExpr",
                "line": line_no,
                "details": {
                    "return_join": str(return_val),
                    "rhs_value": str(rhs_val),
                    "operator": comp_op,
                    **cmp
                },
                "message": f'returnExpression {comp_op} {self._pretty_expr(value_expr)} → {cmp["message"]}',
            }
        except Exception as e:
            return self._err("postRetExpr", f"internal error: {e}", line_no)

    def verify_post_return_variable(self, *, var_ref, comp_op: str, value_expr, line_no: int, fn_cfg):
        try:
            exit_node = fn_cfg.get_exit_node()
            comp_vals = []
            for rv in exit_node.return_vals.values():
                comp_vals.append(self._pick_from_return(rv, var_ref))

            if not comp_vals:
                ret_comp = None
            else:
                acc = comp_vals[0]
                for v in comp_vals[1:]:
                    acc = self._join_values(acc, v)
                ret_comp = self._materialize(acc)

            rhs_val = self._eval_on_exit_value(value_expr, fn_cfg, normal_only=True)

            cmp = self._compare_values(ret_comp, comp_op, rhs_val)
            status = "success" if cmp["satisfied"] else "violation"
            return {
                "status": status,
                "kind": "postRetVar",
                "line": line_no,
                "details": {
                    "variable": self._pretty_expr(var_ref),
                    "return_value": str(ret_comp),
                    "rhs_value": str(rhs_val),
                    "operator": comp_op,
                    **cmp
                },
                "message": f'return {self._pretty_expr(var_ref)} {comp_op} {self._pretty_expr(value_expr)} → {cmp["message"]}',
            }
        except Exception as e:
            return self._err("postRetVar", f"internal error: {e}", line_no)

    def verify_post_direct_comparison(self, *, lhs_expr, comp_op: str, rhs_expr, line_no: int, fn_cfg):
        try:
            lhs_val = self._eval_on_exit_value(lhs_expr, fn_cfg, normal_only=True)
            rhs_val = self._eval_on_exit_value(rhs_expr, fn_cfg, normal_only=True)

            cmp = self._compare_values(lhs_val, comp_op, rhs_val)
            status = "success" if cmp["satisfied"] else "violation"
            return {
                "status": status,
                "kind": "postDirectCmp",
                "line": line_no,
                "details": {
                    "lhs_value": str(lhs_val),
                    "rhs_value": str(rhs_val),
                    "operator": comp_op,
                    **cmp
                },
                "message": f'{self._pretty_expr(lhs_expr)} {comp_op} {self._pretty_expr(rhs_expr)} → {cmp["message"]}',
            }
        except Exception as e:
            return self._err("postDirectCmp", f"internal error: {e}", line_no)

    def verify_post_unchanged(self, *, var_ref, line_no: int, fn_cfg):
        ev = self.analyzer.evaluator
        try:
            entry_env = getattr(fn_cfg, "entry_env", fn_cfg.related_variables)
            entry_val = self._materialize(ev.evaluate_expression(var_ref, entry_env, None, None))

            exit_val = self._eval_on_exit_value(var_ref, fn_cfg, normal_only=True)

            cmp = self._compare_values(entry_val, '==', exit_val)
            status = "success" if cmp["satisfied"] else "violation"
            return {
                "status": status,
                "kind": "postUnchanged",
                "line": line_no,
                "details": {
                    "variable": self._pretty_expr(var_ref),
                    "entry_value": str(entry_val),
                    "exit_value": str(exit_val),
                    **cmp
                },
                "message": f'Unchanged({self._pretty_expr(var_ref)}) → {cmp["message"]}',
            }
        except Exception as e:
            return self._err("postUnchanged", f"internal error: {e}", line_no)

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
        # ───────── Interval ↔ Interval (기존) ─────────
        if hasattr(left, "min_value") and hasattr(right, "min_value"):
            info = self._compare_intervals_prob(left, right, op)
            return {
                "satisfied": info["state"] == "satisfied",
                "violated": info["state"] == "violated",
                "uncertain": info["state"] == "uncertain",
                "confidence": info["confidence"],
                "message": f"{info['state']} (conf={info['confidence']})"
            }

        # ───────── 스칼라 ↔ Interval (주로 in / not in) ─────────
        if not hasattr(left, "min_value") and hasattr(right, "min_value"):
            if op in {"in", "not in"}:
                if right.min_value is None or right.max_value is None:
                    return {"satisfied": False, "violated": True,
                            "uncertain": True, "confidence": 0.0,
                            "message": "interval unknown"}
                inside = right.min_value <= left <= right.max_value
                satisfied = inside if op == "in" else not inside
                return {
                    "satisfied": satisfied,
                    "violated": not satisfied,
                    "uncertain": False,
                    "confidence": 1.0,
                    "message": f"{left} {op} [{right.min_value},{right.max_value}] = {satisfied}"
                }

        # ───────── 스칼라 ↔ 스칼라 (기존 + in/not in 방어) ─────────
        try:
            tbl = {
                '<': lambda a, b: a < b,
                '>': lambda a, b: a > b,
                '<=': lambda a, b: a <= b,
                '>=': lambda a, b: a >= b,
                '==': lambda a, b: a == b,
                '!=': lambda a, b: a != b,
            }
            if op in tbl:
                satisfied = tbl[op](left, right)
            elif op == "in":
                satisfied = left == right  # 스칼라끼리 in 은 동일성으로 취급
            elif op == "not in":
                satisfied = left != right
            else:
                raise ValueError(f"unsupported op {op}")

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

    def _expr_to_str(self, e):  # 간단 문자열 직렬화 helper
        if getattr(e, "identifier", None):
            return e.identifier
        if getattr(e, "member", None):
            return f"{self._expr_to_str(e.base)}.{e.member}"
        if getattr(e, "index", None):
            idx = getattr(e.index, "literal", "?")
            return f"{self._expr_to_str(e.base)}[{idx}]"
        return str(e)

    def _pick_from_return(self, ret_v, var_ref):
        """
        ret_v :  한 줄의 return 값 (Interval, list, tuple …)
        var_ref.context:
            • "ReturnTupleBase"        → 전체 반환
            • "ReturnElemRef"          → return[i]
        """
        # 전체 tuple 그대로
        if var_ref.context == "ReturnTupleBase":
            return ret_v

        # return[ idx ]  ── element 추출
        if var_ref.context == "ReturnElemRef":
            idx = int(var_ref.index.literal, 0)
            if isinstance(ret_v, (list, tuple)) and idx < len(ret_v):
                return ret_v[idx]
            return None
        # 기타 경우는 evaluator 로 해결하도록 위임
        return ret_v

    def _join_values(self, a, b):
        """
        Helper의 _merge_values를 최대한 재사용.
        단, list/tuple/dict 은 Helper가 모르므로 여기서만 얇게 감싸서 원소별 join.
        """
        if a is None: return b
        if b is None: return a

        # list/tuple → 원소별 재귀
        if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
            if len(a) != len(b):
                return "⊤"
            return type(a)(self._join_values(x, y) for x, y in zip(a, b))

        # dict → key union 후 값별 재귀
        if isinstance(a, dict) and isinstance(b, dict):
            keys = set(a) | set(b)
            return {k: self._join_values(a.get(k), b.get(k)) for k in keys}

        # 나머지는 Helper에게 위임(Interval/Variables/Struct/Array/Mapping 등)
        try:
            return VariableEnv._merge_values(a, b, "join")
        except Exception:
            # 서로 다른 Interval형 조합 등에서 join이 예외를 던질 수 있음 → 보수적 ⊤
            return "⊤"

    def _materialize(self, v):
        """
        Variables/Struct/Array/Mapping → 값 뷰로 평탄화
        Interval/스칼라 → 그대로
        """
        if v is None:
            return None
        if hasattr(v, "elements") and isinstance(getattr(v, "elements"), list):  # ArrayVariable
            return [self._materialize(getattr(e, "value", e)) for e in v.elements]
        if hasattr(v, "members") and isinstance(getattr(v, "members"), dict):  # StructVariable
            return {k: self._materialize(getattr(m, "value", m)) for k, m in v.members.items()}
        if hasattr(v, "mapping") and isinstance(getattr(v, "mapping"), dict):  # MappingVariable
            return {k: self._materialize(getattr(m, "value", m)) for k, m in v.mapping.items()}
        if hasattr(v, "value") and not (hasattr(v, "elements") or hasattr(v, "members") or hasattr(v, "mapping")):
            return self._materialize(v.value)
        if isinstance(v, (list, tuple)):
            return type(v)(self._materialize(x) for x in v)
        return v

    # GuardianVerificationEngine.py  ─ GuardianVerificationEngine 클래스 내부

    def _preds(self, fn_cfg, *, normal_only: bool = True):
        """
        EXIT의 predecessor 중 정상 경로만 뽑아옴.
        (빌더에서 revert/require/assert(false) 엣지에 edge['abnormal']=True 를 붙였다고 가정)
        """
        G = fn_cfg.graph
        exit_n = fn_cfg.get_exit_node()
        out = []
        for p in G.predecessors(exit_n):
            ed = G.get_edge_data(p, exit_n, default={})
            if normal_only and ed.get("abnormal"):
                continue
            out.append(p)
        return out

    def _exit_env(self, fn_cfg, *, normal_only: bool = True) -> dict:
        """
        EXIT 직전의 '변수 환경'을 Helper의 join으로 하나로 만든다.
        ⇒ 이후 expr은 이 env로 한 번만 평가하면 됨.
        """
        preds = self._preds(fn_cfg, normal_only=normal_only)
        if not preds:
            # 본문이 비거나 pred가 없으면 entry/fallback 사용
            return VariableEnv.copy_variables(getattr(fn_cfg, "related_variables", {}))

        env = VariableEnv.copy_variables(preds[0].variables)
        for p in preds[1:]:
            env = VariableEnv.join_variables_simple(env, p.variables)
        return env

    def _eval_on_exit_value(self, expr, fn_cfg, *, normal_only: bool = True):
        """
        pred별로 평가해서 값을 join 하지 말고,
        pred들의 env를 Helper join으로 합친 다음 expr을 '한 번'만 평가.
        """
        exit_env = self._exit_env(fn_cfg, normal_only=normal_only)
        val = self.analyzer.evaluator.evaluate_expression(expr, exit_env, None, None)
        return self._materialize(val)


