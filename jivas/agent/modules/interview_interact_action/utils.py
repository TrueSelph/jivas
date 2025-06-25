import re
import logging

logger = logging.getLogger(__name__)
# logging.basicConfig(level=logging.DEBUG) # Uncomment for detailed parsing logs

def parse_condition_string(condition_str: str) -> list:
    condition_str = condition_str.strip()
    
    # Order is crucial: More specific patterns (like those with brackets) first.
    # Field names can contain [\w.-]
    # Values inside lists/ranges are captured and processed further.
    patterns = {
        # field:[min..max]
        "range": r"^([\w.-]+)\s*:\s*\[\s*([\d.-]+)\s*\.\.\s*([\d.-]+)\s*\]$",
        # field:![v1,v2,v3] (non-greedy match for content inside brackets)
        "not_in_list": r"^([\w.-]+)\s*:\s*!\[\s*([^\]]*?)\s*\]$",
        # field:[v1,v2,v3]
        "in_list": r"^([\w.-]+)\s*:\s*\[\s*([^\]]*?)\s*\]$",
        # Standard operators
        "exact_not_equal": r"^([\w.-]+)\s*!:=\s*(.+)$", # Custom, less common
        "not_equal": r"^([\w.-]+)\s*!=\s*(.+)$",
        "exact_equal": r"^([\w.-]+)\s*:=\s*(.+)$",
        "greater_equal": r"^([\w.-]+)\s*>=\s*([\d.-]+)$",
        "less_equal": r"^([\w.-]+)\s*<=\s*([\d.-]+)$",
        "greater_than": r"^([\w.-]+)\s*>\s*([\d.-]+)$",
        "less_than": r"^([\w.-]+)\s*<\s*([\d.-]+)$",
        # Partial equal (colon) MUST be after list/range checks to avoid capturing them.
        "partial_equal": r"^([\w.-]+)\s*:\s*(.+)$",
        "simple_equal": r"^([\w.-]+)\s*=\s*(.+)$", # General equals
    }

    op_mapping = {
        "range": "[..]", "not_in_list": "![]", "in_list": "[]",
        "exact_not_equal": "!=", "not_equal": "!=", "exact_equal": ":=",
        "greater_equal": ">=", "less_equal": "<=", "greater_than": ">", "less_than": "<",
        "partial_equal": ":", "simple_equal": "="
    }

    for op_key, pattern in patterns.items():
        match = re.fullmatch(pattern, condition_str)
        if match:
            # logger.debug(f"Matched op_key '{op_key}' for condition '{condition_str}'")
            field = match.group(1).strip()
            operator_symbol = op_mapping[op_key]

            if op_key == "range":
                # value1 is group 2, value2 is group 3 for range
                val1 = match.group(2).strip()
                val2 = match.group(3).strip()
                return [field, operator_symbol, [val1, val2]]
            elif op_key in ["in_list", "not_in_list"]:
                # values_str is group 2 for lists
                values_str = match.group(2).strip()
                values = [v.strip() for v in values_str.split(',') if v.strip()] if values_str else []
                return [field, operator_symbol, values]
            else: 
                # value_str is group 2 for most other operators
                value_str = match.group(2).strip()
                if value_str.lower() == 'true': value = True
                elif value_str.lower() == 'false': value = False
                else: value = value_str
                return [field, operator_symbol, value]
    
    logger.warning(f"Could not parse condition part: '{condition_str}' with any known pattern.")
    return None

# evaluate_single_condition remains largely the same as the refined version from previous response
def evaluate_single_condition(parsed_condition: list, responses: dict) -> bool:
    if not parsed_condition or len(parsed_condition) < 3:
        logger.warning(f"Invalid parsed condition structure: {parsed_condition}")
        return False 

    field_name, operator, expected_value = parsed_condition[0], parsed_condition[1], parsed_condition[2]
    actual_value_from_responses = responses.get(field_name)

    if actual_value_from_responses is None:
        if operator == "!=" or operator == "![]": return True
        return False
    
    actual_value_str = str(actual_value_from_responses)

    try:
        if operator in ['>', '<', '>=', '<=']:
            actual_val_num = float(actual_value_str)
            expected_val_num = float(expected_value) 
            if operator == '>': return actual_val_num > expected_val_num
            if operator == '<': return actual_val_num < expected_val_num
            if operator == '>=': return actual_val_num >= expected_val_num
            if operator == '<=': return actual_val_num <= expected_val_num
        
        elif operator == '[..]': 
            actual_val_num = float(actual_value_str)
            min_val = float(expected_value[0])
            max_val = float(expected_value[1])
            return min_val <= actual_val_num <= max_val

        elif operator == '=': 
            if isinstance(expected_value, bool):
                return (actual_value_str.lower() == 'true') == expected_value
            try:
                # Handle cases where expected_value might be a string representing a number
                if isinstance(expected_value, str):
                    if (expected_value.lower() == 'true'): return actual_value_str.lower() == 'true'
                    if (expected_value.lower() == 'false'): return actual_value_str.lower() == 'false'
                    if expected_value.replace('.', '', 1).lstrip('-').isdigit():
                         return float(actual_value_str) == float(expected_value)
                # If expected_value is already float/int (less likely from parser)
                elif isinstance(expected_value, (int, float)):
                    return float(actual_value_str) == expected_value

            except ValueError: pass # Fallback to string comparison
            return actual_value_str == str(expected_value)
        
        elif operator == ':=': 
            return actual_value_str == str(expected_value)
            
        elif operator == '!=': 
            if isinstance(expected_value, bool):
                return (actual_value_str.lower() == 'true') != expected_value
            try:
                if isinstance(expected_value, str):
                    if (expected_value.lower() == 'true'): return actual_value_str.lower() != 'true'
                    if (expected_value.lower() == 'false'): return actual_value_str.lower() != 'false'
                    if expected_value.replace('.', '', 1).lstrip('-').isdigit():
                        return float(actual_value_str) != float(expected_value)
                elif isinstance(expected_value, (int, float)):
                     return float(actual_value_str) != expected_value
            except ValueError: pass
            return actual_value_str != str(expected_value)

        elif operator == ':': 
            return str(expected_value).lower() in actual_value_str.lower()

        elif operator == '[]': 
            return actual_value_str in [str(v) for v in expected_value]
            
        elif operator == '![]': 
            return actual_value_str not in [str(v) for v in expected_value]

    except ValueError as e:
        logger.warning(f"Type error during evaluation: field='{field_name}', op='{operator}', actual='{actual_value_str}', expected='{expected_value}'. Error: {e}")
        return False
    
    logger.warning(f"Unhandled operator '{operator}' for field '{field_name}'")
    return False

def evaluate_conditional_expression(expression: str, responses: dict) -> bool:
    """
    Evaluate a conditional string with AND (&&) and OR (||) operators.
    Supports parentheses for grouping.
    OR has lower precedence than AND.
    """
    expression = expression.strip()
    if not expression:
        return True
    
    # Check if this is just a boolean literal (from parentheses processing)
    if expression == 'true':
        return True
    elif expression == 'false':
        return False
    
    # Check if this is a simple condition (no operators)
    if '&&' not in expression and '||' not in expression and '(' not in expression:
        # Simple condition - parse and evaluate directly
        parsed = parse_condition_string(expression)
        if parsed is None:
            return False
        return evaluate_single_condition(parsed, responses)
    
    # Handle parentheses first
    while '(' in expression:
        # Find the innermost parentheses
        start = -1
        for i, char in enumerate(expression):
            if char == '(':
                start = i
            elif char == ')' and start != -1:
                # Found a matching closing paren
                inner_expr = expression[start + 1:i]
                inner_result = evaluate_conditional_expression(inner_expr, responses)
                # Replace the parenthesized expression with its result
                expression = expression[:start] + str(inner_result).lower() + expression[i + 1:]
                break
        else:
            # No matching closing paren found
            logger.error(f"Mismatched parentheses in: {expression}")
            return False
    
    # Now handle OR operations (lower precedence)
    if '||' in expression:
        or_parts = expression.split('||')
        for part in or_parts:
            if evaluate_conditional_expression(part.strip(), responses):
                return True
        return False
    
    # Handle AND operations (higher precedence)
    if '&&' in expression:
        and_parts = expression.split('&&')
        for part in and_parts:
            part = part.strip()
            # It's a condition that needs to be evaluated (boolean literals handled at top)
            if not evaluate_conditional_expression(part, responses):
                return False
        return True
    
    # If we get here, it should be a simple condition
    parsed = parse_condition_string(expression)
    if parsed is None:
        return False
    return evaluate_single_condition(parsed, responses)