"""File handling utils"""

from jvserve.lib.file_interface import (
    FILE_INTERFACE,
    file_interface,
    get_file_interface,
)

# ensure .jvdata is the root as it contains sensitive data which we don't
# want served by jvcli jvfileserve
jvdata_file_interface = (
    get_file_interface("") if FILE_INTERFACE == "local" else file_interface
)
