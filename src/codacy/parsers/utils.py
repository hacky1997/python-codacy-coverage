import os


def get_git_directory():
    import subprocess

    return subprocess.check_output(['git', 'rev-parse', '--show-toplevel']).decode("utf-8").strip()


def file_exists(rootdir, filename):
    for root, subFolders, files in os.walk(rootdir):
        if filename in files:
            return True
        else:
            for subFolder in subFolders:
                return file_exists(os.path.join(rootdir, subFolder), filename)
            return False


def generate_filename(sources, filename, git_directory):
    def strip_prefix(line, prefix):
        if line.startswith(prefix):
            return line[len(prefix):]
        else:
            return line

    if not git_directory:
        git_directory = get_git_directory()

    for source in sources:
        if file_exists(source, filename):
            return strip_prefix(source, git_directory).strip("/") + "/" + filename.strip("/")

    return filename
