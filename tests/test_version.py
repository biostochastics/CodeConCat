import re
from codeconcat.version import __version__

def test_version_format():
    """Test that the version string follows semantic versioning."""
    pattern = r'^\d+\.\d+\.\d+(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?(?:\+[0-9A-Za-z-]+)?$'
    assert re.match(pattern, __version__) is not None
