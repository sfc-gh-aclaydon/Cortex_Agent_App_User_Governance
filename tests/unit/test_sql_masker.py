import unittest
from services.sql_masker import SQLMasker

class TestSQLMasker(unittest.TestCase):
    def setUp(self):
        self.masker = SQLMasker()
    
    def test_mask_security_predicates(self):
        """Test removal of security predicates"""
        sql_with_security = """
        SELECT customer_name, SUM(revenue) 
        FROM sales_data 
        WHERE quarter = 'Q4 2024' 
        AND region_id IN (SELECT region_id FROM get_user_regions())
        GROUP BY customer_name 
        ORDER BY SUM(revenue) DESC
        """
        
        result = self.masker.mask_security_predicates(sql_with_security)
        
        # Should remove security predicates
        self.assertNotIn('get_user_regions', result)
        
        # Should preserve business logic
        self.assertIn('quarter = \'Q4 2024\'', result)
        self.assertIn('customer_name', result)
        self.assertIn('SUM(revenue)', result)
    
    def test_business_predicate_preservation(self):
        """Test that business predicates are preserved"""
        sql = "SELECT * FROM sales_data WHERE product_category = 'Software'"
        result = self.masker.mask_security_predicates(sql)
        self.assertIn('product_category = \'Software\'', result)
    
    def test_session_context_removal(self):
        """Test removal of session context predicates"""
        sql_with_session = """
        SELECT * FROM sales_data 
        WHERE ARRAY_CONTAINS(region_id::VARIANT, PARSE_JSON(GETVARIABLE('ACCESSIBLE_REGIONS')))
        AND product_category = 'Hardware'
        """
        
        result = self.masker.mask_security_predicates(sql_with_session)
        
        # Should remove session context
        self.assertNotIn('GETVARIABLE', result)
        self.assertNotIn('ARRAY_CONTAINS', result)
        self.assertNotIn('accessible_regions', result)
        
        # Should preserve business logic
        self.assertIn('product_category = \'Hardware\'', result)
    
    def test_complex_where_clause(self):
        """Test complex WHERE clause with mixed predicates"""
        sql_complex = """
        SELECT customer_name, revenue, quarter
        FROM sales_data 
        WHERE quarter IN ('Q3 2024', 'Q4 2024') 
        AND revenue > 100000
        AND current_user_id = GETVARIABLE('CURRENT_USER_ID')
        AND product_category != 'Services'
        ORDER BY revenue DESC
        """
        
        result = self.masker.mask_security_predicates(sql_complex)
        
        # Should remove security predicates
        self.assertNotIn('current_user_id', result)
        self.assertNotIn('GETVARIABLE', result)
        
        # Should preserve all business predicates
        self.assertIn('quarter IN (\'Q3 2024\', \'Q4 2024\')', result)
        self.assertIn('revenue > 100000', result)
        self.assertIn('product_category != \'Services\'', result)
    
    def test_no_where_clause(self):
        """Test SQL without WHERE clause"""
        sql_no_where = "SELECT customer_name, SUM(revenue) FROM sales_data GROUP BY customer_name"
        result = self.masker.mask_security_predicates(sql_no_where)
        self.assertEqual(sql_no_where, result)
    
    def test_malformed_sql_fallback(self):
        """Test fallback for malformed SQL"""
        malformed_sql = "SELECT * FROM sales_data WHERE ("
        result = self.masker.mask_security_predicates(malformed_sql)
        
        # Should return fallback message
        self.assertIn('SQL query generated and executed successfully', result)
        self.assertIn('Security filters applied automatically', result)
    
    def test_is_security_predicate(self):
        """Test security predicate identification"""
        # Security predicates
        self.assertTrue(self.masker._is_security_predicate('current_user_id = 123'))
        self.assertTrue(self.masker._is_security_predicate('ARRAY_CONTAINS(region_id, get_user_regions())'))
        self.assertTrue(self.masker._is_security_predicate('GETVARIABLE(\'ACCESSIBLE_REGIONS\')'))
        self.assertTrue(self.masker._is_security_predicate('$current_user_id'))
        
        # Business predicates
        self.assertFalse(self.masker._is_security_predicate('quarter = "Q4 2024"'))
        self.assertFalse(self.masker._is_security_predicate('product_category = "Software"'))
        self.assertFalse(self.masker._is_security_predicate('revenue > 100000'))
    
    def test_format_sql_for_display(self):
        """Test SQL formatting"""
        unformatted_sql = "select customer_name,sum(revenue) from sales_data group by customer_name"
        formatted = self.masker.format_sql_for_display(unformatted_sql)
        
        # Should be properly formatted
        self.assertIn('SELECT', formatted)
        self.assertIn('GROUP BY', formatted)

if __name__ == '__main__':
    unittest.main()
