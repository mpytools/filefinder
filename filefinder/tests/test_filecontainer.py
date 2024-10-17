import pandas as pd
import pytest

from filefinder import FileContainer


@pytest.fixture
def example_df():

    df = pd.DataFrame.from_records(
        [
            ("file0", "a", "d", "r"),
            ("file1", "a", "h", "r"),
            ("file2", "b", "h", "r"),
            ("file3", "b", "d", "r"),
            ("file4", "c", "d", "r"),
        ],
        columns=("path", "model", "scen", "res"),
    ).set_index("path")

    return df


@pytest.fixture
def example_fc(example_df):

    return FileContainer(example_df)


def test_empty_filecontainer():

    df = pd.DataFrame([], columns=["cat"], index=pd.Index([], name="path"))

    fc = FileContainer(df)

    assert fc.df is df
    assert len(fc) == 0

    with pytest.raises(StopIteration):
        next(iter(fc))


def test_filecontainer(example_df, example_fc):

    assert example_fc.df is example_df
    assert len(example_fc) == 5


def test_fc_iter(example_df, example_fc):

    # test one manually
    path, meta = next(iter(example_fc))
    assert path == "file0"
    assert meta == {"model": "a", "scen": "d", "res": "r"}

    result = list(example_fc)
    expected = list(zip(example_df.index.to_list(), example_df.to_dict("records")))
    assert result == expected


def test_filecontainer_search(example_df, example_fc):

    assert len(example_fc.search()) == 0
    assert len(example_fc.search(model="d")) == 0

    result = example_fc.search(model="a")
    expected = example_df.iloc[[0, 1]]
    pd.testing.assert_frame_equal(result.df, expected)

    result = example_fc.search(model=["a", "c"])
    expected = example_df.iloc[[0, 1, 4]]
    pd.testing.assert_frame_equal(result.df, expected)

    result = example_fc.search(model="a", scen="h")
    expected = example_df.iloc[[1]]
    pd.testing.assert_frame_equal(result.df, expected)

    result = example_fc.search(model=["a", "b"], scen="d")
    expected = example_df.iloc[[0, 3]]
    pd.testing.assert_frame_equal(result.df, expected)


def test_fc_combine_by_key_deprecated(example_fc):

    with pytest.warns(FutureWarning, match="`combine_by_key` has been deprecated"):
        example_fc[[0]].combine_by_key()


def test_fc_combine_by_keys(example_fc):

    result = example_fc[[0]]._combine_by_keys()

    # create one manually
    expected = pd.Series(["a.d.r"], index=pd.Index(["file0"], name="path"))
    pd.testing.assert_series_equal(result, expected)

    result = example_fc._combine_by_keys()
    expected = map(".".join, example_fc.df.values)
    expected = pd.Series(expected, index=example_fc.df.index)

    # different sep
    result = example_fc._combine_by_keys(sep="|")
    expected = map("|".join, example_fc.df.values)
    expected = pd.Series(expected, index=example_fc.df.index)

    # not all columns
    result = example_fc._combine_by_keys(keys=("model", "res"))
    expected = map(".".join, example_fc.df[["model", "res"]].values)
    expected = pd.Series(expected, index=example_fc.df.index)
