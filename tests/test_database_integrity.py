import unittest
from sqlalchemy import inspect
from database import init_db, engine, SessionLocal, Payment, Action, StrategyWeight, Exception_
from datetime import datetime, timezone

class TestDatabaseIntegrity(unittest.TestCase):
    def setUp(self):
        init_db()
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_tables_exist(self):
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        self.assertIn("payments", tables)
        self.assertIn("actions", tables)
        self.assertIn("strategy_weights", tables)
        self.assertIn("exceptions", tables)

    def test_payment_crud(self):
        payment = Payment(
            payment_id="test_pay_101",
            amount=1500.0,
            payment_method="upi",
            bank="HDFC",
            customer_id="cust_test_101",
            past_failure_rate=0.1,
            time_of_day=12,
            pincode_tier=1,
            failure_reason="bank_timeout",
            status="pending"
        )
        self.db.add(payment)
        self.db.commit()

        fetched = self.db.query(Payment).filter(Payment.payment_id == "test_pay_101").first()
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.amount, 1500.0)

        # Cleanup
        self.db.delete(fetched)
        self.db.commit()

    def test_action_creation(self):
        action = Action(
            payment_id="test_pay_102",
            attempt_number=1,
            strategy_chosen="retry",
            strategy_weight=0.85,
            reasoning_trace="Test retry reasoning",
            outcome="recovered"
        )
        self.db.add(action)
        self.db.commit()

        fetched = self.db.query(Action).filter(Action.payment_id == "test_pay_102").first()
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.strategy_chosen, "retry")

        self.db.delete(fetched)
        self.db.commit()

    def test_session_rollback_on_error(self):
        db2 = SessionLocal()
        try:
            p1 = Payment(payment_id="dup_1", amount=100.0)
            self.db.add(p1)
            self.db.commit()

            p2 = Payment(payment_id="dup_1", amount=200.0)
            db2.add(p2)
            db2.commit()
        except Exception:
            db2.rollback()
        finally:
            db2.close()

        fetched = self.db.query(Payment).filter(Payment.payment_id == "dup_1").first()
        if fetched:
            self.db.delete(fetched)
            self.db.commit()

if __name__ == "__main__":
    unittest.main()
