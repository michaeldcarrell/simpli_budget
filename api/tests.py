from decimal import Decimal

from django.test import SimpleTestCase

from helpers.splits import SplitError, SplitLine, build_split_lines, parse_amount, remainder


class ParseAmountTests(SimpleTestCase):
    def test_strips_currency_formatting_and_rounds_to_cent(self):
        self.assertEqual(parse_amount('$1,234.565'), Decimal('1234.57'))
        self.assertEqual(parse_amount(12.5), Decimal('12.50'))

    def test_rejects_zero_negative_and_junk(self):
        for value in ('0', '-5', 'abc', None, True, 'NaN', 'Infinity', '0.001'):
            with self.subTest(value=value), self.assertRaises(SplitError):
                parse_amount(value)


class BuildSplitLinesTests(SimpleTestCase):
    def test_lines_take_the_transaction_sign(self):
        # Plaid: outflows positive, inflows negative.
        self.assertEqual(
            build_split_lines(Decimal('100.00'), 1, [{'category_id': 2, 'amount': '30'}]),
            [SplitLine(2, Decimal('30.00'))],
        )
        self.assertEqual(
            build_split_lines(Decimal('-100.00'), 1, [{'category_id': 2, 'amount': '30'}]),
            [SplitLine(2, Decimal('-30.00'))],
        )

    def test_remainder_is_what_the_lines_leave(self):
        lines = build_split_lines(Decimal('100.00'), 1, [
            {'category_id': 2, 'amount': '33.33'},
            {'category_id': 3, 'amount': '33.33'},
        ])
        self.assertEqual(remainder(Decimal('100.00'), lines), Decimal('33.34'))

    def test_lines_may_use_the_whole_amount(self):
        lines = build_split_lines(Decimal('-50.00'), 1, [
            {'category_id': 2, 'amount': '20'},
            {'category_id': 3, 'amount': '30'},
        ])
        self.assertEqual(remainder(Decimal('-50.00'), lines), Decimal('0.00'))

    def test_over_allocation_is_refused(self):
        with self.assertRaisesRegex(SplitError, 'more than'):
            build_split_lines(Decimal('100.00'), 1, [
                {'category_id': 2, 'amount': '60'},
                {'category_id': 3, 'amount': '40.01'},
            ])

    def test_duplicate_or_own_category_is_refused(self):
        with self.assertRaises(SplitError):
            build_split_lines(Decimal('100'), 1, [{'category_id': 2, 'amount': 1}, {'category_id': 2, 'amount': 1}])
        with self.assertRaises(SplitError):
            build_split_lines(Decimal('100'), 1, [{'category_id': 1, 'amount': 1}])

    def test_string_category_ids_are_accepted(self):
        self.assertEqual(build_split_lines(Decimal('10'), 1, [{'category_id': '2', 'amount': 1}])[0].category_id, 2)

    def test_bad_input_is_refused(self):
        for total, lines in (
            (Decimal('0'), [{'category_id': 2, 'amount': 1}]),
            (Decimal('10'), []),
            (Decimal('10'), None),
            (Decimal('10'), ['x']),
            (Decimal('10'), [{'category_id': None, 'amount': 1}]),
            (Decimal('10'), [{'category_id': True, 'amount': 1}]),
        ):
            with self.subTest(total=total, lines=lines), self.assertRaises(SplitError):
                build_split_lines(total, 1, lines)


class DevLoginGateTests(SimpleTestCase):
    """The Google-free dev sign-in must not exist outside a dev server (simpli_budget/settings.py)."""

    def test_not_routed_unless_enabled(self):
        from django.conf import settings
        from django.urls import Resolver404, resolve
        self.assertFalse(settings.DEV_LOGIN_ENABLED)  # tests run without DEV_LOGIN
        with self.assertRaises(Resolver404):
            resolve('/dev-login')

    def test_view_refuses_when_disabled(self):
        from django.http import Http404
        from django.test import RequestFactory, override_settings
        from simpli_budget.views import DevLogin
        with override_settings(DEV_LOGIN_ENABLED=False), self.assertRaises(Http404):
            DevLogin.as_view()(RequestFactory().post('/dev-login', {'user_id': 1}))

    def test_requires_debug_and_a_dev_database(self):
        import importlib
        import os
        from unittest import mock
        import simpli_budget.settings as settings_module
        cases = (
            ({'DEV_LOGIN': 'True', 'DEBUG': 'True', 'CBA_POSTGRES_DB_NAME': 'simplibudget_dev'}, True),
            ({'DEV_LOGIN': 'True', 'DEBUG': 'False', 'CBA_POSTGRES_DB_NAME': 'simplibudget_dev'}, False),
            ({'DEV_LOGIN': 'True', 'DEBUG': 'True', 'CBA_POSTGRES_DB_NAME': 'simplibudget'}, False),
            ({'DEV_LOGIN': 'False', 'DEBUG': 'True', 'CBA_POSTGRES_DB_NAME': 'simplibudget_dev'}, False),
        )
        try:
            for env, expected in cases:
                with self.subTest(env=env), mock.patch.dict(os.environ, env):
                    self.assertEqual(importlib.reload(settings_module).DEV_LOGIN_ENABLED, expected)
        finally:
            importlib.reload(settings_module)
