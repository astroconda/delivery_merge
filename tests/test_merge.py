import pytest
from delivery_merge import merge


COMMENTS_DELIM = [';', '#']
COMMENTS = """; comment
; comment ; comment
;comment;comment
;comment#comment
data  ; comment
data ; comment
data; comment
data;comment
# comment
# comment # comment
#comment#comment
#comment;comment
data  # comment
data # comment
data# comment
data#comment
"""
DMFILE = """
; Example
python  # dmfile
nomkl
numpy>=1.16.3

"""
DMFILE_INVALID = f"""
{DMFILE}
invalid package specification
"""

class TestMerge:
    def setup_class(self):
        self.input_file = 'sample.dm'
        self.input_file_invalid = 'sample_invalid.dm'
        self.input_file_empty = 'sample_empty.dm'
        open(self.input_file, 'w+').write(DMFILE)
        open(self.input_file_invalid, 'w+').write(DMFILE_INVALID)
        open(self.input_file_empty, 'w+').write("")

    def teardown_class(self):
        pass

    @pytest.mark.parametrize('comments', [x for x in COMMENTS.splitlines()])
    def test_comment_find(self, comments):
        index = merge.comment_find(comments)
        assert comments[index] in COMMENTS_DELIM

    def test_dmfile(self):
        data = merge.dmfile(self.input_file)
        assert COMMENTS_DELIM not in data
        assert all([merge.DMFILE_RE.match(x) for x in data])

    def test_dmfile_raises_InvalidPackageSpec(self):
        with pytest.raises(merge.InvalidPackageSpec):
            merge.dmfile(self.input_file_invalid)

    def test_dmfile_raises_EmptyPackageSpec(self):
        with pytest.raises(merge.EmptyPackageSpec):
            merge.dmfile(self.input_file_empty)
