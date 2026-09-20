import json
import unittest
from datetime import datetime
import backend
from app import app

class TestExpenseTracker(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        backend.init_tracker()

    def test_01_index_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Expense Tracker', response.data)

    def test_02_get_expenses(self):
        response = self.client.get('/api/expenses')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)

    def test_03_add_and_summary(self):
        payload = {
            'good_or_service': 'Stationery & Notebooks',
            'price': 450.0,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'expense_type': 'SCHOOL FEE'
        }
        res_add = self.client.post('/api/add', json=payload)
        self.assertEqual(res_add.status_code, 200)
        res_json = json.loads(res_add.data)
        self.assertTrue(res_json['success'])

        # Check summary
        res_sum = self.client.get('/api/summary')
        self.assertEqual(res_sum.status_code, 200)
        sum_data = json.loads(res_sum.data)
        self.assertGreater(sum_data['total_expense'], 0)
        self.assertIn('SCHOOL FEE', sum_data['category_breakdown'])

    def test_04_export_csv_and_jpeg(self):
        # CSV Export
        res_csv = self.client.get('/api/export/csv?type=all')
        self.assertEqual(res_csv.status_code, 200)
        self.assertIn('text/csv', res_csv.headers['Content-Type'])

        # JPEG Export
        res_jpeg = self.client.get('/api/export/jpeg?type=DAILY')
        self.assertEqual(res_jpeg.status_code, 200)
        self.assertIn('image/jpeg', res_jpeg.headers['Content-Type'])

    def test_05_ai_insights(self):
        res = self.client.get('/api/ai/insights?budget=25000&risk=BALANCED')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['success'])
        self.assertIn('monthly_comparison', data)
        self.assertIn('peer_benchmarking', data)
        self.assertIn('investment_plan', data)
        self.assertIn('smart_insights', data)
        
        # Check investment plan allocation
        allocations = data['investment_plan']['allocations']
        self.assertEqual(len(allocations), 4)
        asset_keys = [a['asset_class'] for a in allocations]
        self.assertIn('GOLD', asset_keys)
        self.assertIn('INFRA', asset_keys)
        self.assertIn('STOCKS', asset_keys)
        self.assertIn('EMERGENCY', asset_keys)

    def test_06_ai_advisor(self):
        res = self.client.post('/api/ai/advisor', json={'query': 'Where to invest surplus budget in gold and stocks?'})
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['success'])
        self.assertIn('Gold', data['response'])
        self.assertIn('Infrastructure', data['response'])
        self.assertIn('Stock Market', data['response'])

if __name__ == '__main__':
    unittest.main()

