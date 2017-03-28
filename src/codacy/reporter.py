"""Codacy coverage reporter for Python"""

import argparse
import contextlib
import json
import logging

import os
import requests
from requests.packages.urllib3 import util as urllib3_util
from parsers.cobertura import parse_report_file as parse_cobertura_report_file

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

CODACY_PROJECT_TOKEN = os.getenv('CODACY_PROJECT_TOKEN')
CODACY_BASE_API_URL = os.getenv('CODACY_API_BASE_URL', 'https://api.codacy.com')
URL = CODACY_BASE_API_URL + '/2.0/coverage/{commit}/python'
DEFAULT_REPORT_FILE = 'coverage.xml'
MAX_RETRIES = 3
BAD_REQUEST = 400


class _Retry(urllib3_util.Retry):
    def is_forced_retry(self, method, status_code):
        return status_code >= BAD_REQUEST


@contextlib.contextmanager
def _request_session():
    retry = _Retry(total=MAX_RETRIES, raise_on_redirect=False)
    session = requests.Session()
    session.mount("https://", requests.adapters.HTTPAdapter(max_retries=retry))
    with session:
        yield session


def get_git_revision_hash():
    import subprocess

    return subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode("utf-8").strip()


def merge_and_round_reports(report_list):
    """Merges together several report structures from parse_report_file (and rounds all values)"""

    if len(report_list) == 1:
        final_report = report_list[0]
    else:
        final_report = {
            'language': "python",
            'fileReports': []
        }

        total_lines = 0
        for report in report_list:
            # First, merge together detailed report structures
            # This assumes no overlap
            # TODO: What should we do if there is a file listed multiple times?
            final_report['fileReports'] += report['fileReports']
            total_lines += report['codeLines']

        # Coverage weighted average (by number of lines of code) of all files
        average_sum = 0
        for file_entry in final_report['fileReports']:
            average_sum += file_entry['total'] * file_entry['codeLines']

        final_report['total'] = average_sum / total_lines
        final_report['codeLines'] = total_lines

    # Round all total values
    for file_entry in final_report['fileReports']:
        file_entry['total'] = int(file_entry['total'])
    final_report['total'] = int(final_report['total'])

    return final_report


def upload_report(report, token, commit):
    """Try to send the data, raise an exception if we fail"""
    url = URL.format(commit=commit)
    data = json.dumps(report)
    headers = {
        "project_token": token,
        "Content-Type": "application/json"
    }

    logging.debug(data)

    with _request_session() as session:
        r = session.post(url, data=data, headers=headers, allow_redirects=True)

    logging.debug(r.content)
    r.raise_for_status()

    response = json.loads(r.text)

    try:
        logging.info(response['success'])
    except KeyError:
        logging.error(response['error'])


def run():
    parser = argparse.ArgumentParser(description='Codacy coverage reporter for Python.')
    parser.add_argument("-r", "--report", help="coverage report file",
                        default=[], type=str,
                        action='append')
    parser.add_argument("-c", "--commit", type=str, help="git commit hash")
    parser.add_argument("-d", "--directory", type=str, help="git top level directory")
    parser.add_argument("-v", "--verbose", help="show debug information", action="store_true")

    args = parser.parse_args()

    if args.verbose:
        logging.Logger.setLevel(logging.getLogger(), logging.DEBUG)

    if not CODACY_PROJECT_TOKEN:
        logging.error("environment variable CODACY_PROJECT_TOKEN is not defined.")
        exit(1)

    if not args.commit:
        args.commit = get_git_revision_hash()

    if not args.report:
        args.report.append(DEFAULT_REPORT_FILE)

    # Explictly check ALL files before parsing any
    for rfile in args.report:
        if not os.path.isfile(rfile):
            logging.error("Coverage report " + rfile + " not found.")
            exit(1)

    reports = []
    for rfile in args.report:
        logging.info("Parsing report file %s...", rfile)
        reports.append(parse_cobertura_report_file(rfile, args.directory))

    report = merge_and_round_reports(reports)

    logging.info("Uploading report...")
    upload_report(report, CODACY_PROJECT_TOKEN, args.commit)
