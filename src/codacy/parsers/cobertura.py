from xml.dom import minidom
from utils import *


def parse_report_file(report_file, git_directory):
    """Parse XML file and POST it to the Codacy API
    :param report_file:
    :param git_directory:
    """

    # Convert decimal string to decimal percent value
    def percent(s):
        return float(s) * 100

    # Parse the XML into the format expected by the API
    report_xml = minidom.parse(report_file)

    report = {
        'language': "python",
        'total': percent(report_xml.getElementsByTagName('coverage')[0].attributes['line-rate'].value),
        'fileReports': [],
    }

    sources = [x.firstChild.nodeValue for x in report_xml.getElementsByTagName('source')]
    classes = report_xml.getElementsByTagName('class')
    total_lines = 0
    for cls in classes:
        lines = cls.getElementsByTagName('line')
        total_lines += len(lines)
        file_report = {
            'filename': generate_filename(sources, cls.attributes['filename'].value, git_directory),
            'total': percent(cls.attributes['line-rate'].value),
            'codeLines': len(lines),
            'coverage': {},
        }
        for line in lines:
            hits = int(line.attributes['hits'].value)
            if hits >= 1:
                # The API assumes 0 if a line is missing
                file_report['coverage'][line.attributes['number'].value] = hits
        report['fileReports'] += [file_report]

    report['codeLines'] = total_lines

    return report

