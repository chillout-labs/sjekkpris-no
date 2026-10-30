"""Exact link-only exception: no generic protected-page mutation permission."""
import unittest
from tools.beta_navigation import PLAN, adjust, approved_change, descriptor


class BetaNavigationTests(unittest.TestCase):
    def setUp(self):
        self.raw = b'<a class="card" href="https://sjekkpris.no/p/test/">Keep design and text</a>'
        self.expected = b'<a class="card" href="/k/">Keep design and text</a>'
        self.plan = dict(before=descriptor(self.raw, 'beta/example/index.html'),
                         after=descriptor(self.expected, 'beta/example/index.html'),
                         links=['https://sjekkpris.no/p/test/'], target='/k/', count=1)

    def test_only_exact_href_changes(self):
        self.assertEqual(adjust(self.raw, {'/p/test/'}, self.plan), self.expected)

    def test_changed_input_or_missing_retirement_refused(self):
        for raw, routes in ((self.raw+b' ', {'/p/test/'}), (self.raw, set())):
            with self.assertRaises(ValueError):
                adjust(raw, routes, self.plan)

    def test_wrong_count_or_output_refused(self):
        for plan in (dict(self.plan, count=2), dict(self.plan, target='/other/')):
            with self.assertRaises(ValueError):
                adjust(self.raw, {'/p/test/'}, plan)

    def test_preservation_exception_is_exact_and_one_way(self):
        self.assertTrue(approved_change(PLAN['before'], PLAN['after']))
        self.assertFalse(approved_change(PLAN['after'], PLAN['before']))
        self.assertFalse(approved_change(PLAN['before'], dict(PLAN['after'], sha256='0'*64)))
        self.assertFalse(approved_change(dict(PLAN['before'], path='beta/other.html'), PLAN['after']))
