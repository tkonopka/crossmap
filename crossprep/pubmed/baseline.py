"""Downloading baseline article data from pubmed.

@author: Tomasz Konopka
"""

import time
from os.path import join
from .tools import parse_indexes, ensure_dir, download_one


def template_format(template):
    """Parse template string to identify digit formatting,
    e.g. a template med#####.xml.gz will give output (#####, {:05})
    """

    num_hashes = sum([1 for c in template if c == "#"])
    return "#"*num_hashes, "{:0" + str(num_hashes) + "}"


def download_baseline(config):
    """Run downloads for baseline files from pubmed."""
    
    out_dir = ensure_dir(join(config.outdir, "baseline"))

    # Download the README
    url = config.url
    if not url.endswith("/"):
        url += "/"
    readme_url = url + "README.txt"
    download_one(readme_url, join(out_dir, "README.txt"))
    
    # try to download files
    template = config.template
    hashes, format = template_format(template)

    if config.indexes is None:
        config.indexes = "1-2000"
    for i in parse_indexes(config.indexes):
        file_name = template.replace(hashes, format.format(i))
        file_path = join(out_dir, file_name)
        status = download_one(url+file_name, file_path)
        # stop if file does not exist, or continue
        if status == 404:
            break
        if status == 200:
            time.sleep(config.sleep)


