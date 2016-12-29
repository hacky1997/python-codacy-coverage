import json
import os
import unittest

import codacy.reporter

HERE = os.path.abspath(os.path.dirname(__file__))


def _file_location(*args):
    return os.path.join(HERE, *args)


class ReporterTests(unittest.TestCase):
    def compare_parse_result(self, generated, expected_filename):
        def file_get_contents(filename):
            with open(filename) as f:
                return f.read()

        json_content = file_get_contents(expected_filename)
        expected = json.loads(json_content)

        self.assertEqual(generated, expected)

    def test_parser_coverage3(self):
        self.maxDiff = None

        parsed = codacy.reporter.parse_report_file(
            _file_location('coverage3', 'cobertura.xml'), '')

        rounded = codacy.reporter.merge_and_round_reports([parsed])

        self.compare_parse_result(rounded,
                                  _file_location('coverage3', 'coverage.json'))

    def test_parser_coverage4(self):
        self.maxDiff = None

        parsed = codacy.reporter.parse_report_file(
            _file_location('coverage4', 'cobertura.xml'), '')

        rounded = codacy.reporter.merge_and_round_reports([parsed])

        self.compare_parse_result(rounded,
                                  _file_location('coverage4', 'coverage.json'))

    def test_parser_git_filepath(self):
        self.maxDiff = None

        parsed = codacy.reporter.parse_report_file(
            _file_location('filepath', 'cobertura.xml.tpl'), '')

        rounded = codacy.reporter.merge_and_round_reports([parsed])

        self.compare_parse_result(rounded,
                                  _file_location('filepath', 'coverage.json'))

    def test_merge(self):
        self.maxDiff = None

        generated3 = codacy.reporter.parse_report_file(
            _file_location('coverage-merge', 'cobertura.3.xml'), '')
        generated4 = codacy.reporter.parse_report_file(
            _file_location('coverage-merge', 'cobertura.4.xml'), '')

        result = codacy.reporter.merge_and_round_reports([generated3, generated4])

        self.compare_parse_result(result, _file_location('coverage-merge', 'coverage-merge.json'))


if __name__ == '__main__':
    unittest.main()
