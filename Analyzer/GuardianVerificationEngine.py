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
    """
    Verification engine for during and post intent directives.
    Handles temporal state comparisons (Before/After, Entry/Exit).
    """
    
    def __init__(self, analyzer: "ContractAnalyzer"):
        self.analyzer = analyzer
        
    def verify_during_before_after(self, var_ref: str, comp_op: str, line_no: int) -> Dict[str, Any]:
        """
        Verify @During varRef(Before compOp After) assertion.
        
        Args:
            var_ref: Variable reference (e.g., "balance", "accounts[user].amount")
            comp_op: Comparison operator ('<', '>', '<=', '>=', '==', '!=')
            line_no: Source line number
            
        Returns:
            Dict with verification result and details
        """
        try:
            # Get current CFG node from brace_count
            node_info = self.analyzer.brace_count.get(line_no, {})
            current_node = node_info.get('cfg_node')
            
            if not current_node or not hasattr(current_node, 'variables'):
                return {
                    'status': 'error',
                    'message': f'No CFG node found for line {line_no}',
                    'line': line_no
                }
            
            # Get current variable state (After)
            current_vars = current_node.variables
            after_value = self._resolve_var_ref(var_ref, current_vars)
            
            if after_value is None:
                return {
                    'status': 'error', 
                    'message': f'Variable {var_ref} not found in current state',
                    'line': line_no
                }
            
            # Get before value by looking at predecessor nodes
            before_value = self._get_before_value(current_node, var_ref)
            
            if before_value is None:
                return {
                    'status': 'warning',
                    'message': f'Cannot determine before value for {var_ref}',
                    'line': line_no
                }
            
            # Perform comparison
            result = self._compare_values(before_value, comp_op, after_value)
            
            return {
                'status': 'success' if result['satisfied'] else 'violation',
                'message': f'During check: {var_ref}(Before {comp_op} After) = {result["message"]}',
                'details': {
                    'variable': var_ref,
                    'before_value': str(before_value),
                    'after_value': str(after_value),
                    'operator': comp_op,
                    'satisfied': result['satisfied']
                },
                'line': line_no
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error in during before/after check: {str(e)}',
                'line': line_no
            }
    
    def verify_during_assign_current(self, var_ref: str, comp_op: str, intent_expr: Any, line_no: int) -> Dict[str, Any]:
        """
        Verify @During varRef(Assign compOp Current) assertion.
        
        Args:
            var_ref: Variable reference
            comp_op: Comparison operator
            intent_expr: Expression to compare against
            line_no: Source line number
        """
        try:
            node_info = self.analyzer.brace_count.get(line_no, {})
            current_node = node_info.get('cfg_node')
            
            if not current_node:
                return {
                    'status': 'error',
                    'message': f'No CFG node found for line {line_no}',
                    'line': line_no
                }
            
            # Get assigned value (what was just assigned)
            assigned_value = self._get_assigned_value(current_node, var_ref)
            
            # Get current value (after assignment)
            current_vars = current_node.variables
            current_value = self._resolve_var_ref(var_ref, current_vars)
            
            if assigned_value is None or current_value is None:
                return {
                    'status': 'warning',
                    'message': f'Cannot determine assign/current values for {var_ref}',
                    'line': line_no
                }
            
            # Evaluate intent expression
            expected_value = self._evaluate_intent_expression(intent_expr, current_vars)
            
            # Compare assigned value with expected
            result = self._compare_values(assigned_value, comp_op, expected_value)
            
            return {
                'status': 'success' if result['satisfied'] else 'violation',
                'message': f'During assign check: {var_ref}(Assign {comp_op} Current) = {result["message"]}',
                'details': {
                    'variable': var_ref,
                    'assigned_value': str(assigned_value),
                    'current_value': str(current_value),
                    'expected_value': str(expected_value),
                    'operator': comp_op,
                    'satisfied': result['satisfied']
                },
                'line': line_no
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error in during assign/current check: {str(e)}',
                'line': line_no
            }
    
    def verify_during_return_expression(self, comp_op: str, intent_expr: Any, line_no: int) -> Dict[str, Any]:
        """
        Verify @During returnExpression compOp intentExpression assertion.
        """
        try:
            node_info = self.analyzer.brace_count.get(line_no, {})
            current_node = node_info.get('cfg_node')
            
            if not current_node:
                return {
                    'status': 'error',
                    'message': f'No CFG node found for line {line_no}',
                    'line': line_no
                }
            
            # Get return expression from current statement
            return_value = self._get_return_expression_value(current_node)
            
            if return_value is None:
                return {
                    'status': 'warning',
                    'message': 'No return expression found in current context',
                    'line': line_no
                }
            
            # Evaluate intent expression
            expected_value = self._evaluate_intent_expression(intent_expr, current_node.variables)
            
            # Compare
            result = self._compare_values(return_value, comp_op, expected_value)
            
            return {
                'status': 'success' if result['satisfied'] else 'violation',
                'message': f'During return check: returnExpression {comp_op} {intent_expr} = {result["message"]}',
                'details': {
                    'return_value': str(return_value),
                    'expected_value': str(expected_value),
                    'operator': comp_op,
                    'satisfied': result['satisfied']
                },
                'line': line_no
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error in during return expression check: {str(e)}',
                'line': line_no
            }
    
    def verify_post_entry_exit(self, var_ref: str, comp_op: str, line_no: int) -> Dict[str, Any]:
        """
        Verify @Post varRef(Entry compOp Exit) assertion.
        Operates on function exit node.
        """
        try:
            # Get current function CFG
            function_cfg = self.analyzer.current_target_function_cfg
            if not function_cfg:
                return {
                    'status': 'error',
                    'message': 'No current function context found',
                    'line': line_no
                }
            
            exit_node = function_cfg.get_exit_node()
            
            # Get entry value (from function entry)
            entry_node = function_cfg.get_entry_node()
            entry_value = self._resolve_var_ref(var_ref, entry_node.variables)
            
            # Get exit value (join of all predecessors of exit node)
            exit_vars = self._join_predecessor_variables(exit_node, function_cfg)
            exit_value = self._resolve_var_ref(var_ref, exit_vars)
            
            if entry_value is None or exit_value is None:
                return {
                    'status': 'warning',
                    'message': f'Cannot determine entry/exit values for {var_ref}',
                    'line': line_no
                }
            
            # Compare
            result = self._compare_values(entry_value, comp_op, exit_value)
            
            return {
                'status': 'success' if result['satisfied'] else 'violation',
                'message': f'Post check: {var_ref}(Entry {comp_op} Exit) = {result["message"]}',
                'details': {
                    'variable': var_ref,
                    'entry_value': str(entry_value),
                    'exit_value': str(exit_value),
                    'operator': comp_op,
                    'satisfied': result['satisfied']
                },
                'line': line_no
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error in post entry/exit check: {str(e)}',
                'line': line_no
            }
    
    def verify_post_return_values(self, comp_op: str, intent_expr: Any, line_no: int) -> Dict[str, Any]:
        """
        Verify @Post returnValues compOp intentExpression assertion.
        Checks join of all return values.
        """
        try:
            function_cfg = self.analyzer.current_target_function_cfg
            if not function_cfg:
                return {
                    'status': 'error',
                    'message': 'No current function context found',
                    'line': line_no
                }
            
            exit_node = function_cfg.get_exit_node()
            
            # Join return values from all predecessors
            return_values = self._join_return_values(exit_node, function_cfg)
            
            if not return_values:
                return {
                    'status': 'warning',
                    'message': 'No return values found',
                    'line': line_no
                }
            
            # Evaluate intent expression against exit state
            exit_vars = self._join_predecessor_variables(exit_node, function_cfg)
            expected_value = self._evaluate_intent_expression(intent_expr, exit_vars)
            
            # Compare joined return values with expected
            result = self._compare_values(return_values, comp_op, expected_value)
            
            return {
                'status': 'success' if result['satisfied'] else 'violation',
                'message': f'Post return values check: returnValues {comp_op} {intent_expr} = {result["message"]}',
                'details': {
                    'return_values': str(return_values),
                    'expected_value': str(expected_value),
                    'operator': comp_op,
                    'satisfied': result['satisfied']
                },
                'line': line_no
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error in post return values check: {str(e)}',
                'line': line_no
            }
    
    def verify_post_unchanged(self, var_ref: str, line_no: int) -> Dict[str, Any]:
        """
        Verify @Post Unchanged(varRef) assertion.
        """
        try:
            function_cfg = self.analyzer.current_target_function_cfg
            if not function_cfg:
                return {
                    'status': 'error',
                    'message': 'No current function context found',
                    'line': line_no
                }
            
            entry_node = function_cfg.get_entry_node()
            exit_node = function_cfg.get_exit_node()
            
            # Get entry and exit values
            entry_value = self._resolve_var_ref(var_ref, entry_node.variables)
            exit_vars = self._join_predecessor_variables(exit_node, function_cfg)
            exit_value = self._resolve_var_ref(var_ref, exit_vars)
            
            if entry_value is None or exit_value is None:
                return {
                    'status': 'warning',
                    'message': f'Cannot determine entry/exit values for {var_ref}',
                    'line': line_no
                }
            
            # Check if unchanged (equality)
            unchanged = self._values_equal(entry_value, exit_value)
            
            return {
                'status': 'success' if unchanged else 'violation',
                'message': f'Post unchanged check: Unchanged({var_ref}) = {"satisfied" if unchanged else "violated"}',
                'details': {
                    'variable': var_ref,
                    'entry_value': str(entry_value),
                    'exit_value': str(exit_value),
                    'unchanged': unchanged
                },
                'line': line_no
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error in post unchanged check: {str(e)}',
                'line': line_no
            }
    
    # Helper Methods
    
    def _resolve_var_ref(self, var_ref: str, variables: Dict[str, Variables]) -> Any:
        """
        Resolve variable reference like "balance" or "accounts[user].amount"
        """
        # Simple case: direct variable
        if var_ref in variables:
            var_obj = variables[var_ref]
            return getattr(var_obj, 'value', var_obj)
        
        # Complex case: member access, array access, etc.
        # This would need more sophisticated parsing of var_ref
        # For now, try simple dot notation
        if '.' in var_ref:
            parts = var_ref.split('.', 1)
            base_var = parts[0]
            member = parts[1]
            
            if base_var in variables:
                base_obj = variables[base_var]
                if hasattr(base_obj, 'members') and member in base_obj.members:
                    return getattr(base_obj.members[member], 'value', base_obj.members[member])
        
        return None
    
    def _get_before_value(self, current_node: CFGNode, var_ref: str) -> Any:
        """
        Get the value of var_ref before the current statement.
        Look at predecessor nodes or statement history.
        """
        # Simple approach: if current node has statements,
        # look at variable state before the last statement
        if hasattr(current_node, 'statements') and current_node.statements:
            # For now, return the current value as approximation
            # In a full implementation, we'd track statement-level changes
            return self._resolve_var_ref(var_ref, current_node.variables)
        
        return None
    
    def _get_assigned_value(self, current_node: CFGNode, var_ref: str) -> Any:
        """
        Get the value that was just assigned to var_ref.
        """
        # Look through statements in current node for assignments
        if hasattr(current_node, 'statements'):
            for stmt in reversed(current_node.statements):  # Most recent first
                if (hasattr(stmt, 'statement_type') and 
                    stmt.statement_type == 'assignment' and
                    hasattr(stmt, 'left')):
                    # Check if this assignment targets var_ref
                    if (hasattr(stmt.left, 'identifier') and 
                        stmt.left.identifier == var_ref):
                        # Return the right-hand side value
                        if hasattr(stmt, 'right'):
                            return self._evaluate_expression(stmt.right, current_node.variables)
        
        return None
    
    def _get_return_expression_value(self, current_node: CFGNode) -> Any:
        """
        Get return expression value from current node.
        """
        if hasattr(current_node, 'statements'):
            for stmt in reversed(current_node.statements):
                if (hasattr(stmt, 'statement_type') and 
                    stmt.statement_type == 'return' and
                    hasattr(stmt, 'return_expr')):
                    return self._evaluate_expression(stmt.return_expr, current_node.variables)
        
        return None
    
    def _join_predecessor_variables(self, node: CFGNode, cfg) -> Dict[str, Variables]:
        """
        Join variable states from all predecessor nodes.
        """
        predecessors = list(cfg.graph.predecessors(node))
        if not predecessors:
            return {}
        
        # Start with first predecessor's variables
        joined_vars = VariableEnv.copy_variables(predecessors[0].variables)
        
        # Join with remaining predecessors
        for pred in predecessors[1:]:
            joined_vars = VariableEnv.join_variables_simple(joined_vars, pred.variables)
        
        return joined_vars
    
    def _join_return_values(self, exit_node: CFGNode, cfg) -> Any:
        """
        Join return values from all paths leading to exit.
        """
        predecessors = list(cfg.graph.predecessors(exit_node))
        return_values = []
        
        for pred in predecessors:
            if hasattr(pred, 'return_vals') and pred.return_vals:
                # Collect all return values
                for ret_val in pred.return_vals.values():
                    return_values.append(ret_val)
        
        if not return_values:
            return None
        
        # For now, return first value or join them if multiple
        if len(return_values) == 1:
            return return_values[0]
        
        # Join multiple return values (simplified)
        result = return_values[0]
        for val in return_values[1:]:
            if hasattr(result, 'join'):
                result = result.join(val)
        
        return result
    
    def _evaluate_intent_expression(self, intent_expr: Any, variables: Dict[str, Variables]) -> Any:
        """
        Evaluate an intent expression in the context of given variables.
        """
        # This would use the existing expression evaluation logic
        # For now, simple placeholder
        if hasattr(intent_expr, 'literal'):
            return intent_expr.literal
        
        if hasattr(intent_expr, 'identifier'):
            return self._resolve_var_ref(intent_expr.identifier, variables)
        
        return intent_expr
    
    def _evaluate_expression(self, expr: Expression, variables: Dict[str, Variables]) -> Any:
        """
        Evaluate an expression using the analyzer's evaluation logic.
        """
        if hasattr(self.analyzer, 'evaluator'):
            return self.analyzer.evaluator.evaluate_expression(expr, variables)
        
        # Fallback: simple evaluation
        if hasattr(expr, 'literal'):
            return expr.literal
        
        if hasattr(expr, 'identifier'):
            return self._resolve_var_ref(expr.identifier, variables)
        
        return None
    
    def _compare_values(self, left: Any, op: str, right: Any) -> Dict[str, Any]:
        """
        Compare two values using the given operator.
        Returns dict with 'satisfied' boolean and 'message' string.
        """
        try:
            # Handle interval comparisons
            if hasattr(left, 'compare') and hasattr(right, 'compare'):
                # Both are intervals - use interval arithmetic
                if op == '<':
                    satisfied = left.max_value < right.min_value if hasattr(left, 'max_value') else False
                elif op == '>':
                    satisfied = left.min_value > right.max_value if hasattr(left, 'min_value') else False
                elif op == '<=':
                    satisfied = left.max_value <= right.min_value if hasattr(left, 'max_value') else False
                elif op == '>=':
                    satisfied = left.min_value >= right.max_value if hasattr(left, 'min_value') else False
                elif op == '==':
                    satisfied = (hasattr(left, 'min_value') and hasattr(left, 'max_value') and
                               left.min_value == left.max_value == right.min_value == right.max_value)
                elif op == '!=':
                    satisfied = not (hasattr(left, 'min_value') and hasattr(left, 'max_value') and
                                   left.min_value == left.max_value == right.min_value == right.max_value)
                else:
                    satisfied = False
            else:
                # Simple value comparison
                if op == '<':
                    satisfied = left < right
                elif op == '>':
                    satisfied = left > right
                elif op == '<=':
                    satisfied = left <= right
                elif op == '>=':
                    satisfied = left >= right
                elif op == '==':
                    satisfied = left == right
                elif op == '!=':
                    satisfied = left != right
                else:
                    satisfied = False
            
            return {
                'satisfied': satisfied,
                'message': f'{left} {op} {right} = {satisfied}'
            }
            
        except Exception as e:
            return {
                'satisfied': False,
                'message': f'Comparison error: {str(e)}'
            }
    
    def _values_equal(self, left: Any, right: Any) -> bool:
        """
        Check if two values are equal, handling intervals and other types.
        """
        try:
            if hasattr(left, 'equals') and hasattr(right, 'equals'):
                return left.equals(right)
            
            return left == right
            
        except:
            return False