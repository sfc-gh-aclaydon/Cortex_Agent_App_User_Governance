import re
import sqlparse
from typing import List
from sqlparse.sql import IdentifierList, Identifier, Where
from sqlparse.tokens import Keyword, Whitespace

class SQLMasker:
    def __init__(self):
        # Patterns that indicate security-related predicates
        self.security_patterns = [
            r'region_id\s*(?:=|IN)\s*(?:\d+|\([^)]+\))',  # region_id filters
            r'GETVARIABLE\([^)]+\)',                       # session variable access
            r'get_user_regions\(\)',                       # custom security functions
            r'accessible_regions',                         # session variables
            r'current_user_id',                           # user context
            r'ARRAY_CONTAINS\([^)]+\)',                   # array operations for regions
            r'PARSE_JSON\(\s*GETVARIABLE\([^)]+\)\)',     # JSON session parsing
            r'\$[a-zA-Z_][a-zA-Z0-9_]*',                  # $variable_name syntax
        ]
    
    def mask_security_predicates(self, sql_statement: str) -> str:
        """
        Remove security-related WHERE clauses from SQL statement
        while preserving business logic predicates
        """
        try:
            # Parse the SQL statement
            parsed = sqlparse.parse(sql_statement)[0]
            
            # Find WHERE clause
            where_clause = self._find_where_clause(parsed)
            if not where_clause:
                return sql_statement
            
            # Extract and filter predicates
            business_predicates = self._extract_business_predicates(where_clause)
            
            # Reconstruct SQL with only business predicates
            if business_predicates:
                clean_sql = self._reconstruct_sql_with_predicates(sql_statement, business_predicates)
            else:
                clean_sql = self._remove_where_clause(sql_statement)
            
            return clean_sql
            
        except Exception as e:
            # If masking fails, return a generic message
            return "-- SQL query generated and executed successfully\n-- (Security filters applied automatically)"
    
    def _find_where_clause(self, parsed_sql):
        """Find the WHERE clause in parsed SQL"""
        for token in parsed_sql.tokens:
            if isinstance(token, Where):
                return token
        return None
    
    def _extract_business_predicates(self, where_clause):
        """Extract non-security predicates from WHERE clause"""
        where_text = str(where_clause)
        
        # Split by AND/OR to get individual predicates
        # This is a simplified approach - in production you'd want more robust parsing
        predicates = re.split(r'\s+(?:AND|OR)\s+', where_text, flags=re.IGNORECASE)
        
        business_predicates = []
        for predicate in predicates:
            if not self._is_security_predicate(predicate):
                business_predicates.append(predicate.strip())
        
        return business_predicates
    
    def _is_security_predicate(self, predicate: str) -> bool:
        """Check if a predicate is security-related"""
        predicate_lower = predicate.lower()
        
        # Check against security patterns
        for pattern in self.security_patterns:
            if re.search(pattern, predicate, re.IGNORECASE):
                return True
        
        # Additional heuristics for security predicates
        security_keywords = [
            'getvariable',
            'get_user_regions',
            'accessible_regions',
            'current_user_id',
            'array_contains',
            'parse_json'
        ]
        
        for keyword in security_keywords:
            if keyword in predicate_lower:
                return True
        
        return False
    
    def _reconstruct_sql_with_predicates(self, original_sql: str, business_predicates: List[str]) -> str:
        """Reconstruct SQL with only business predicates in WHERE clause"""
        try:
            # Find WHERE clause position
            where_match = re.search(r'\bWHERE\b', original_sql, re.IGNORECASE)
            if not where_match:
                return original_sql
            
            # Find the end of WHERE clause (before ORDER BY, GROUP BY, HAVING, etc.)
            where_start = where_match.end()
            
            # Look for clause endings
            clause_endings = ['ORDER BY', 'GROUP BY', 'HAVING', 'LIMIT', 'OFFSET']
            where_end = len(original_sql)
            
            for ending in clause_endings:
                match = re.search(f'\\b{ending}\\b', original_sql[where_start:], re.IGNORECASE)
                if match:
                    where_end = where_start + match.start()
                    break
            
            # Reconstruct SQL
            before_where = original_sql[:where_match.start()]
            after_where = original_sql[where_end:]
            
            if business_predicates:
                # Clean and join business predicates
                clean_predicates = []
                for pred in business_predicates:
                    # Remove WHERE keyword if present
                    pred = re.sub(r'^\s*WHERE\s+', '', pred, flags=re.IGNORECASE)
                    if pred.strip():
                        clean_predicates.append(pred.strip())
                
                if clean_predicates:
                    new_where = "WHERE " + " AND ".join(clean_predicates)
                    return before_where + new_where + " " + after_where
            
            # No business predicates, remove WHERE clause entirely
            return before_where + after_where
            
        except Exception:
            # Fallback to simple WHERE removal
            return self._remove_where_clause(original_sql)
    
    def _remove_where_clause(self, sql_statement: str) -> str:
        """Remove entire WHERE clause from SQL statement"""
        # Simple regex to remove WHERE clause
        pattern = r'\bWHERE\b.*?(?=\b(?:ORDER BY|GROUP BY|HAVING|LIMIT|OFFSET|$))'
        cleaned = re.sub(pattern, '', sql_statement, flags=re.IGNORECASE | re.DOTALL)
        
        # Clean up extra whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned
    
    def format_sql_for_display(self, sql_statement: str) -> str:
        """Format SQL for better display to users"""
        try:
            # Parse and format the SQL
            formatted = sqlparse.format(
                sql_statement,
                reindent=True,
                keyword_case='upper',
                identifier_case='lower',
                strip_comments=False
            )
            return formatted
        except Exception:
            return sql_statement
