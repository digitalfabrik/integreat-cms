from shutil import rmtree

from dev import cms_package_dir
from dev.utils import print_info


def pdf_cache_evict() -> None:
    cache_dir = cms_package_dir / "pdf"
    print_info(f"➡ Evict PDF cache ({cache_dir})")
    rmtree(cache_dir, ignore_errors=True)
