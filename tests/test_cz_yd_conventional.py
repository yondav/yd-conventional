import unittest
from unittest import mock

from cz_yd_conventional import YDConventional


def make_plugin():
    return YDConventional.__new__(YDConventional)


class TestYDConventional(unittest.TestCase):
    def test_parse_scope_adds_ref_prefix(self):
        plugin = make_plugin()
        self.assertEqual(plugin.parse_scope("YD-123"), "ref YD-123")

    def test_parse_scope_keeps_existing_ref_prefix(self):
        plugin = make_plugin()
        self.assertEqual(plugin.parse_scope("ref YD-123"), "ref YD-123")

    def test_parse_scope_hyphenates_non_issue_scope(self):
        plugin = make_plugin()
        self.assertEqual(plugin.parse_scope("my feature area"), "my-feature-area")

    def test_parse_subject_strips_trailing_period(self):
        plugin = make_plugin()
        self.assertEqual(plugin.parse_subject("add new api."), "add new api")

    def test_message_formats_breaking_change(self):
        plugin = make_plugin()
        answers = {
            "commit_type": "feat",
            "commit_scope": "ref YD-10",
            "commit_subject": "add audit log",
            "commit_body": "includes user and role metadata",
            "commit_footer": "ref YD-11",
            "commit_breaking": True,
        }
        expected = (
            "feat(ref YD-10): add audit log\n\n"
            "includes user and role metadata\n\n"
            "BREAKING CHANGE: ref YD-11"
        )
        self.assertEqual(plugin.message(answers), expected)

    def test_read_issue_id_from_branch_detects_linear_key(self):
        plugin = make_plugin()
        with mock.patch("cz_yd_conventional.os.popen") as popen:
            mock_proc = mock.MagicMock()
            mock_proc.read.return_value = "feature/YD-123-add-login"
            popen.return_value.__enter__.return_value = mock_proc
            self.assertEqual(plugin.read_issue_id_from_branch(), "ref YD-123")


if __name__ == "__main__":
    unittest.main()
