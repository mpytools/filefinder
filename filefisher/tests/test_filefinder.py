import os
import textwrap

import pandas as pd
import pytest

from filefisher import FileFinder
from filefisher._filefinder import _assert_unique

from . import assert_filecontainer_empty


@pytest.fixture(scope="module")
def tmp_path(tmp_path_factory):
    return tmp_path_factory.mktemp("filefisher")


@pytest.fixture(scope="module", autouse=True)
def path(tmp_path):
    """
    Creates the following temporary structure:
    - /tmp/filefisher/a1/foo/file
    - /tmp/filefisher/a2/foo/file
    """

    d = tmp_path / "a1" / "foo"
    d.mkdir(parents=True)
    f = d / "file"
    f.write_text("")

    d = tmp_path / "a2" / "foo"
    d.mkdir(parents=True)
    f = d / "file"
    f.write_text("")

    return tmp_path


@pytest.fixture(scope="module", params=["from_filesystem", "from_string"])
def test_paths(request, tmp_path):

    if request.param == "from_filesystem":
        return None

    paths = ["a1/foo/file", "a2/foo/file"]
    paths = [str(tmp_path / path) for path in paths]

    return paths


@pytest.mark.parametrize("placeholder", ("keys", "on_parse_error", "_allow_empty"))
def test_pattern_invalid_placeholder(placeholder):

    with pytest.raises(ValueError, match=f"'{placeholder}' is not a valid placeholder"):
        FileFinder("", f"{{{placeholder}}}")

    with pytest.raises(ValueError, match=f"'{placeholder}' is not a valid placeholder"):
        FileFinder(f"{{{placeholder}}}", "")


@pytest.mark.parametrize("pattern", ("{}", "{_fixed}"))
def test_only_named_fields(pattern):

    with pytest.raises(ValueError, match="Only named fields are currently allowed"):
        FileFinder("", pattern)

    with pytest.raises(ValueError, match="Only named fields are currently allowed"):
        FileFinder(pattern, "")


def test_assert_unique():

    # no error raised
    df = pd.DataFrame.from_records([("a", "d"), ("a", "h")], columns=("model", "res"))
    _assert_unique(df)

    df = pd.DataFrame.from_records([("a", "d"), ("a", "d")], columns=("model", "res"))
    with pytest.raises(ValueError, match="Non-unique metadata detected"):
        _assert_unique(df)


@pytest.mark.parametrize("_allow_empty", (False, True))
def test_deprecate_allow_empty(_allow_empty):

    ff = FileFinder("", "a")
    msg = "`_allow_empty` has been deprecated in favour of `on_empty`"
    with pytest.raises(TypeError, match=msg):
        ff.find_files(_allow_empty=_allow_empty)

    with pytest.raises(TypeError, match=msg):
        ff.find_paths(_allow_empty=_allow_empty)


def test_wrong_on_empty():

    ff = FileFinder("", "a")
    msg = "Unknown value for 'on_empty': 'null'. Must be one of 'raise', 'warn' or 'allow'."
    with pytest.raises(ValueError, match=msg):
        ff.find_paths(on_empty="null")

    with pytest.raises(ValueError, match=msg):
        ff.find_files(on_empty="null")


def test_pattern_property():

    path_pattern = "path_pattern/"
    file_pattern = "file_pattern"

    ff = FileFinder(path_pattern=path_pattern, file_pattern=file_pattern)

    assert ff.path_pattern == path_pattern
    assert ff.file_pattern == file_pattern

    assert ff._full_pattern == path_pattern + file_pattern

    assert ff.path.pattern == path_pattern
    assert ff.file.pattern == file_pattern

    assert ff.full.pattern == path_pattern + file_pattern


def test_test_path_property():

    ff = FileFinder("a", "b")

    with pytest.raises(AttributeError):
        ff._test_paths

    ff = FileFinder("a", "b", test_paths="path")
    assert ff._test_paths == ["path"]

    ff = FileFinder("a", "b", test_paths=["a", "b"])
    assert ff._test_paths == ["a", "b"]


def test_test_path_assert_nonunique():

    with pytest.raises(ValueError, match="`test_paths` are not unique"):
        FileFinder("a", "", test_paths=["a", "a"])

    with pytest.raises(ValueError, match="`test_paths` are not unique"):
        FileFinder("a", "", test_paths=["a/", "a/"])

    with pytest.raises(ValueError, match="`test_paths` are not unique"):
        FileFinder("a", "", test_paths=["a/b", "a/b"])


def test_file_pattern_no_sep():

    path_pattern = "path_pattern"
    file_pattern = "file" + os.path.sep + "pattern"

    with pytest.raises(ValueError, match="cannot contain path separator"):
        FileFinder(path_pattern=path_pattern, file_pattern=file_pattern)


def test_pattern_sep_added():

    path_pattern = "path_pattern"
    file_pattern = "file_pattern"

    ff = FileFinder(path_pattern=path_pattern, file_pattern=file_pattern)
    assert ff.path_pattern == path_pattern + os.path.sep


def test_keys():

    file_pattern = "{a}_{b}_{c}"
    path_pattern = "{ab}_{c}"
    ff = FileFinder(path_pattern=path_pattern, file_pattern=file_pattern)

    expected = ("ab", "c", "a", "b")
    assert ff.keys == expected

    expected = ("a", "b", "c")
    assert ff.keys_file == expected

    expected = ("ab", "c")
    assert ff.keys_path == expected


def test_repr():

    path_pattern = "/{a}/{b}"
    file_pattern = "{b}_{c}"
    ff = FileFinder(path_pattern=path_pattern, file_pattern=file_pattern)

    expected = """\
    <FileFinder>
    path_pattern: '/{a}/{b}/'
    file_pattern: '{b}_{c}'

    keys: 'a', 'b', 'c'
    """
    expected = textwrap.dedent(expected)
    assert expected == ff.__repr__()

    path_pattern = "{a}"
    file_pattern = "file_pattern"
    ff = FileFinder(path_pattern=path_pattern, file_pattern=file_pattern)

    expected = """\
    <FileFinder>
    path_pattern: '{a}/'
    file_pattern: 'file_pattern'

    keys: 'a'
    """
    expected = textwrap.dedent(expected)
    assert expected == ff.__repr__()


def test_create_name():

    path_pattern = "{a}/{b}"
    file_pattern = "{b}_{c}"
    ff = FileFinder(path_pattern=path_pattern, file_pattern=file_pattern)

    result = ff.create_path_name(a="a", b="b")
    assert result == "a/b/"

    result = ff.create_file_name(b="b", c="c")
    assert result == "b_c"

    result = ff.create_full_name(a="a", b="b", c="c")
    assert result == "a/b/b_c"


def test_create_name_dict():

    path_pattern = "{a}/{b}"
    file_pattern = "{b}_{c}"
    ff = FileFinder(path_pattern=path_pattern, file_pattern=file_pattern)

    result = ff.create_path_name(dict(a="a", b="b"))
    assert result == "a/b/"

    result = ff.create_file_name(dict(b="b", c="c"))
    assert result == "b_c"

    result = ff.create_full_name(dict(a="a", b="b", c="c"))
    assert result == "a/b/b_c"


def test_create_name_kwargs_priority():

    path_pattern = "{a}/{b}"
    file_pattern = "{b}_{c}"
    ff = FileFinder(path_pattern=path_pattern, file_pattern=file_pattern)

    result = ff.create_path_name(dict(a="XXX", b="b"), a="a")
    assert result == "a/b/"

    result = ff.create_file_name(dict(b="XXX", c="c"), b="b")
    assert result == "b_c"

    result = ff.create_full_name(dict(a="XXX", b="b"), a="a", c="c")
    assert result == "a/b/b_c"


def test_find_path_none_found(tmp_path, test_paths):

    path_pattern = tmp_path / "{a}/foo/"
    file_pattern = "file_pattern"

    ff = FileFinder(
        path_pattern=path_pattern, file_pattern=file_pattern, test_paths=test_paths
    )

    with pytest.raises(ValueError, match="Found no files matching criteria"):
        ff.find_paths(a="foo")

    with pytest.raises(ValueError, match="Found no files matching criteria"):
        ff.find_paths({"a": "foo"})

    with pytest.warns(match="Found no files matching criteria"):
        result = ff.find_paths(a="foo", on_empty="warn")
    assert_filecontainer_empty(result, columns="a")

    with pytest.warns(match="Found no files matching criteria"):
        result = ff.find_paths({"a": "foo"}, on_empty="warn")
    assert_filecontainer_empty(result, columns="a")

    result = ff.find_paths(a="foo", on_empty="allow")
    assert_filecontainer_empty(result, columns="a")

    result = ff.find_paths({"a": "foo"}, on_empty="allow")
    assert_filecontainer_empty(result, columns="a")


def test_find_paths_non_unique():

    # ensure find_paths works for duplicated folder names (made unique by the file name)

    ff = FileFinder("{cat}", "", test_paths=["a/a", "a/b"])

    result = ff.find_paths()

    expected = {"path": {0: "a/*"}, "cat": {0: "a"}}
    expected = pd.DataFrame.from_dict(expected).set_index("path")
    pd.testing.assert_frame_equal(result.df, expected)


def test_find_paths_simple(tmp_path, test_paths):

    path_pattern = tmp_path / "a1/{a}/"
    file_pattern = "file_pattern"

    ff = FileFinder(
        path_pattern=path_pattern, file_pattern=file_pattern, test_paths=test_paths
    )

    expected = {"path": {0: str(tmp_path / "a1/foo/*")}, "a": {0: "foo"}}
    expected = pd.DataFrame.from_dict(expected).set_index("path")

    result = ff.find_paths(a="foo")
    pd.testing.assert_frame_equal(result.df, expected)

    result = ff.find_paths(dict(a="foo"))
    pd.testing.assert_frame_equal(result.df, expected)

    result = ff.find_paths(dict(a="XXX"), a="foo")
    pd.testing.assert_frame_equal(result.df, expected)


@pytest.mark.parametrize("find_kwargs", [{"b": "foo"}, {"a": "*", "b": "foo"}])
def test_find_paths_wildcard(tmp_path, test_paths, find_kwargs):

    path_pattern = tmp_path / "{a}/{b}"
    file_pattern = "file_pattern"

    ff = FileFinder(
        path_pattern=path_pattern, file_pattern=file_pattern, test_paths=test_paths
    )

    expected = {
        "path": {0: str(tmp_path / "a1/foo/*"), 1: str(tmp_path / "a2/foo/*")},
        "a": {0: "a1", 1: "a2"},
        "b": {0: "foo", 1: "foo"},
    }
    expected = pd.DataFrame.from_dict(expected).set_index("path")

    result = ff.find_paths(**find_kwargs)
    pd.testing.assert_frame_equal(result.df, expected)

    result = ff.find_paths(find_kwargs)
    pd.testing.assert_frame_equal(result.df, expected)

    result = ff.find_paths({"b": "XXX"}, **find_kwargs)
    pd.testing.assert_frame_equal(result.df, expected)


@pytest.mark.parametrize(
    "find_kwargs",
    [{"a": ["a1", "a2"], "b": "foo"}, {"a": ["a1", "a2"], "b": ["foo", "bar"]}],
)
def test_find_paths_several(tmp_path, test_paths, find_kwargs):

    path_pattern = tmp_path / "{a}/{b}"
    file_pattern = "file_pattern"

    ff = FileFinder(
        path_pattern=path_pattern, file_pattern=file_pattern, test_paths=test_paths
    )

    expected = {
        "path": {0: str(tmp_path / "a1/foo/*"), 1: str(tmp_path / "a2/foo/*")},
        "a": {0: "a1", 1: "a2"},
        "b": {0: "foo", 1: "foo"},
    }
    expected = pd.DataFrame.from_dict(expected).set_index("path")

    result = ff.find_paths(**find_kwargs)
    pd.testing.assert_frame_equal(result.df, expected)

    result = ff.find_paths(find_kwargs)
    pd.testing.assert_frame_equal(result.df, expected)

    result = ff.find_paths({"a": "XXX", "b": "XXX"}, **find_kwargs)
    pd.testing.assert_frame_equal(result.df, expected)


@pytest.mark.parametrize(
    "find_kwargs",
    [{"a": "a1"}, {"a": "a1", "b": "foo"}, {"a": "a1", "b": ["foo", "bar"]}],
)
def test_find_paths_one_of_several(tmp_path, test_paths, find_kwargs):

    path_pattern = tmp_path / "{a}/{b}"
    file_pattern = "file_pattern"

    ff = FileFinder(
        path_pattern=path_pattern, file_pattern=file_pattern, test_paths=test_paths
    )

    expected = {
        "path": {0: str(tmp_path / "a1/foo/*")},
        "a": {0: "a1"},
        "b": {0: "foo"},
    }
    expected = pd.DataFrame.from_dict(expected).set_index("path")

    result = ff.find_paths(**find_kwargs)
    pd.testing.assert_frame_equal(result.df, expected)

    result = ff.find_paths(find_kwargs)
    pd.testing.assert_frame_equal(result.df, expected)

    result = ff.find_paths({"a": "XXX"}, **find_kwargs)
    pd.testing.assert_frame_equal(result.df, expected)


def test_find_single_path(tmp_path, test_paths):

    path_pattern = tmp_path / "{a}/foo"
    file_pattern = "file_pattern"

    ff = FileFinder(
        path_pattern=path_pattern, file_pattern=file_pattern, test_paths=test_paths
    )

    # error if more than one is found
    with pytest.raises(ValueError, match=r"Found more than one \(2\) files/ paths"):
        ff.find_single_path()

    # error if more than one is found
    with pytest.raises(ValueError, match="Found no files matching criteria"):
        ff.find_single_path(a="a3")

    expected = {"path": {0: str(tmp_path / "a1/foo/*")}, "a": {0: "a1"}}
    expected = pd.DataFrame.from_dict(expected).set_index("path")

    result = ff.find_single_path(a="a1")
    pd.testing.assert_frame_equal(result.df, expected)

    result = ff.find_single_path({"a": "a1"})
    pd.testing.assert_frame_equal(result.df, expected)


def test_find_file_none_found(tmp_path, test_paths):

    path_pattern = tmp_path / "{a}/foo/"
    file_pattern = "{file_pattern}"

    ff = FileFinder(
        path_pattern=path_pattern, file_pattern=file_pattern, test_paths=test_paths
    )

    with pytest.raises(ValueError, match="Found no files matching criteria"):
        ff.find_files(a="XXX")

    with pytest.raises(ValueError, match="Found no files matching criteria"):
        ff.find_files({"a": "XXX"})

    with pytest.warns(match="Found no files matching criteria"):
        result = ff.find_files(a="XXX", on_empty="warn")
    assert_filecontainer_empty(result, columns=("a", "file_pattern"))

    with pytest.warns(match="Found no files matching criteria"):
        result = ff.find_files({"a": "XXX"}, on_empty="warn")
    assert_filecontainer_empty(result, columns=("a", "file_pattern"))

    result = ff.find_files(a="XXX", on_empty="allow")
    assert_filecontainer_empty(result, columns=("a", "file_pattern"))

    result = ff.find_files({"a": "XXX"}, on_empty="allow")
    assert_filecontainer_empty(result, columns=("a", "file_pattern"))

    result = ff.find_files({"a": "XXX"}, on_empty="allow", a="XXX")
    assert_filecontainer_empty(result, columns=("a", "file_pattern"))


def test_find_files_non_unique():

    # test raises error for non-unique metadata - AFAIK not possible for real paths

    ff = FileFinder("", "{cat}")
    # need to set via `_set_test_paths` to avoid duplicate check
    ff._set_test_paths(test_paths=["/a", "/a"])

    with pytest.raises(ValueError, match="Non-unique metadata detected"):
        ff.find_files()


def test_find_file_simple(tmp_path, test_paths):

    path_pattern = tmp_path / "a1/{a}/"
    file_pattern = "file"

    ff = FileFinder(
        path_pattern=path_pattern, file_pattern=file_pattern, test_paths=test_paths
    )

    expected = {"path": {0: str(tmp_path / "a1/foo/file")}, "a": {0: "foo"}}
    expected = pd.DataFrame.from_dict(expected).set_index("path")

    result = ff.find_files(a="foo")
    pd.testing.assert_frame_equal(result.df, expected)

    result = ff.find_files({"a": "foo"})
    pd.testing.assert_frame_equal(result.df, expected)

    result = ff.find_files({"a": "XXX"}, a="foo")
    pd.testing.assert_frame_equal(result.df, expected)


@pytest.mark.parametrize("find_kwargs", [{"b": "file"}, {"a": "*", "b": "file"}])
def test_find_files_wildcard(tmp_path, test_paths, find_kwargs):

    path_pattern = tmp_path / "{a}/foo"
    file_pattern = "{b}"

    ff = FileFinder(
        path_pattern=path_pattern, file_pattern=file_pattern, test_paths=test_paths
    )

    expected = {
        "path": {
            0: str(tmp_path / "a1/foo/file"),
            1: str(tmp_path / "a2/foo/file"),
        },
        "a": {0: "a1", 1: "a2"},
        "b": {0: "file", 1: "file"},
    }
    expected = pd.DataFrame.from_dict(expected).set_index("path")

    result = ff.find_files(**find_kwargs)
    pd.testing.assert_frame_equal(result.df, expected)

    result = ff.find_files(find_kwargs)
    pd.testing.assert_frame_equal(result.df, expected)

    result = ff.find_files({"b": "XXX"}, **find_kwargs)
    pd.testing.assert_frame_equal(result.df, expected)


@pytest.mark.parametrize(
    "find_kwargs",
    [{"a": ["a1", "a2"], "b": "file"}, {"a": ["a1", "a2"], "b": ["file", "bar"]}],
)
def test_find_files_several(tmp_path, test_paths, find_kwargs):

    path_pattern = tmp_path / "{a}/foo"
    file_pattern = "{b}"

    ff = FileFinder(
        path_pattern=path_pattern, file_pattern=file_pattern, test_paths=test_paths
    )

    expected = {
        "path": {
            0: str(tmp_path / "a1/foo/file"),
            1: str(tmp_path / "a2/foo/file"),
        },
        "a": {0: "a1", 1: "a2"},
        "b": {0: "file", 1: "file"},
    }
    expected = pd.DataFrame.from_dict(expected).set_index("path")

    result = ff.find_files(**find_kwargs)
    pd.testing.assert_frame_equal(result.df, expected)

    result = ff.find_files(find_kwargs)
    pd.testing.assert_frame_equal(result.df, expected)

    result = ff.find_files({"a": "XXX", "b": "XXX"}, **find_kwargs)
    pd.testing.assert_frame_equal(result.df, expected)


@pytest.mark.parametrize(
    "find_kwargs",
    [{"a": "a1"}, {"a": "a1", "b": "file"}, {"a": "a1", "b": ["file", "bar"]}],
)
def test_find_files_one_of_several(tmp_path, test_paths, find_kwargs):

    path_pattern = tmp_path / "{a}/foo"
    file_pattern = "{b}"

    ff = FileFinder(
        path_pattern=path_pattern, file_pattern=file_pattern, test_paths=test_paths
    )

    expected = {
        "path": {0: str(tmp_path / "a1/foo/file")},
        "a": {0: "a1"},
        "b": {0: "file"},
    }
    expected = pd.DataFrame.from_dict(expected).set_index("path")

    result = ff.find_files(**find_kwargs)
    pd.testing.assert_frame_equal(result.df, expected)

    result = ff.find_files(find_kwargs)
    pd.testing.assert_frame_equal(result.df, expected)

    result = ff.find_files({"a": "XXX"}, **find_kwargs)
    pd.testing.assert_frame_equal(result.df, expected)


def test_find_single_file(tmp_path, test_paths):

    path_pattern = tmp_path / "{a}/foo"
    file_pattern = "file"

    ff = FileFinder(
        path_pattern=path_pattern, file_pattern=file_pattern, test_paths=test_paths
    )

    # error if more than one is found
    with pytest.raises(ValueError, match=r"Found more than one \(2\) files/ paths"):
        ff.find_single_file()

    # error if more than one is found
    with pytest.raises(ValueError, match="Found no files matching criteria"):
        ff.find_single_file(a="a3")

    expected = {"path": {0: str(tmp_path / "a1/foo/file")}, "a": {0: "a1"}}
    expected = pd.DataFrame.from_dict(expected).set_index("path")

    result = ff.find_single_file(a="a1")
    pd.testing.assert_frame_equal(result.df, expected)

    result = ff.find_single_file({"a": "a1"})
    pd.testing.assert_frame_equal(result.df, expected)


def test_find_paths_scalar_number():

    ff = FileFinder(
        path_pattern="{path}", file_pattern="{file}", test_paths=["1/1", "2/2"]
    )

    index = pd.Index(["1/*"], name="path")
    expected = pd.DataFrame(["1"], columns=["path"], index=index)
    result = ff.find_paths(path=1)
    pd.testing.assert_frame_equal(result.df, expected)


def test_find_files_scalar_number():

    ff = FileFinder(
        path_pattern="{path}", file_pattern="{file}", test_paths=["1/1", "2/2"]
    )

    index = pd.Index(["1/1"], name="path")
    expected = pd.DataFrame([["1", "1"]], columns=["path", "file"], index=index)
    result = ff.find_files(file=1)
    pd.testing.assert_frame_equal(result.df, expected)


def test_find_unparsable():

    ff = FileFinder("{cat}", "{cat}", test_paths=["a/b"])

    with pytest.raises(
        ValueError, match="Could not parse 'a/b' with the pattern '{cat}/{cat}'"
    ):
        ff.find_files()

    expected = pd.DataFrame([], columns=["cat"], index=pd.Index([], name="path"))

    with pytest.warns(match="Could not parse 'a/b' with the pattern '{cat}/{cat}'"):
        result = ff.find_files(on_parse_error="warn")
    pd.testing.assert_frame_equal(result.df, expected)

    result = ff.find_files(on_parse_error="ignore")
    pd.testing.assert_frame_equal(result.df, expected)

    ff = FileFinder("{cat}", "{cat}", test_paths=["a/b", "a/a"])
    expected = {"path": {0: "a/a"}, "cat": {0: "a"}}
    expected = pd.DataFrame.from_dict(expected).set_index("path")
    result = ff.find_files(on_parse_error="ignore")
    pd.testing.assert_frame_equal(result.df, expected)

    with pytest.warns(match="Could not parse 'a/b' with the pattern '{cat}/{cat}'"):
        result = ff.find_files(on_parse_error="warn")
    pd.testing.assert_frame_equal(result.df, expected)

    with pytest.raises(
        ValueError, match="Could not parse 'a/b' with the pattern '{cat}/{cat}'"
    ):
        ff.find_files(on_parse_error="raise")

    with pytest.raises(
        ValueError,
        match="Unknown value for 'on_parse_error': 'foo'. Must be one of 'raise', 'warn' or 'ignore'.",
    ):
        ff.find_files(on_parse_error="foo")

    ff = FileFinder("", "{cat}_{cat}", test_paths=["a_b"])

    with pytest.raises(
        ValueError, match="Could not parse 'a_b' with the pattern '{cat}_{cat}'"
    ):
        ff.find_files()

    ff = FileFinder("{cat}_{cat}", "", test_paths=["a_b/"])

    with pytest.raises(
        ValueError, match="Could not parse 'a_b/' with the pattern '{cat}_{cat}'"
    ):
        ff.find_files()

    with pytest.raises(
        ValueError, match="Could not parse 'a_b/' with the pattern '{cat}_{cat}/'"
    ):
        ff.find_paths()
