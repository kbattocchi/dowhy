import random

import networkx as nx
import numpy as np
import pandas as pd
import pytest
from _pytest.python_api import approx

from dowhy import gcm
from dowhy.gcm.util.general import (
    apply_one_hot_encoding,
    fit_one_hot_encoders,
    has_categorical,
    is_categorical,
    set_random_seed,
    setdiff2d,
    shape_into_2d,
)


@pytest.fixture
def preserve_random_generator_state():
    numpy_state = np.random.get_state()
    random_state = random.getstate()
    yield
    np.random.set_state(numpy_state)
    random.setstate(random_state)


def test_given_categorical_data_when_evaluating_is_categorical_then_returns_expected_result():
    assert is_categorical(np.array(["A", "B", "A"]))
    assert is_categorical(np.array([True, False, False]))
    assert is_categorical(pd.DataFrame({"X": [True, False, False]}).to_numpy())
    assert not is_categorical(np.array([1, 2, 3]))


def test_given_categorical_data_when_evaluating_has_categorical_then_returns_expected_result():
    assert has_categorical(np.array([["A", 2, 3], ["B", 4, 5]]))
    assert has_categorical(
        np.column_stack([np.array([True, False, False], dtype=object), np.array([1, 2, 3], dtype=object)])
    )
    assert has_categorical(pd.DataFrame({"X": [True, False, False], "Y": [1, 2, 3]}).to_numpy())
    assert not has_categorical(np.array([[1, 2, 3], [12.2, 2.3, 3.231]]))


def test_given_categorical_data_when_fit_one_hot_encoders_and_apply_one_hot_encoding_then_returns_expected_feature_vector():
    data = np.array([["d", 1, "a"], ["b", 2, "d"], ["a", 3, "a"]], dtype=object)
    encoders = fit_one_hot_encoders(data)

    assert apply_one_hot_encoding(data, encoders) == approx(
        np.array([[0, 0, 1, 1, 1, 0], [0, 1, 0, 2, 0, 1], [1, 0, 0, 3, 1, 0]])
    )


def test_given_unknown_categorical_input_when_apply_one_hot_encoders_then_does_not_raise_error():
    assert apply_one_hot_encoding(
        np.array([["a", 4, "f"]]),
        fit_one_hot_encoders(np.array([["d", 1, "a"], ["b", 2, "d"], ["a", 3, "a"]], dtype=object)),
    ) == approx(np.array([[1, 0, 0, 4, 0, 0]]))


def test_when_apply_shape_into_2d_then_returns_correct_shape():
    assert shape_into_2d(np.array(1)) == np.array([[1]])
    assert np.all(shape_into_2d(np.array([1, 2, 3, 4])) == np.array([[1], [2], [3], [4]]))
    assert np.all(shape_into_2d(np.array([[1], [2], [3], [4]])) == np.array([[1], [2], [3], [4]]))
    assert np.all(
        shape_into_2d(np.array([[1, 2], [1, 2], [1, 2], [1, 2]])) == np.array([[1, 2], [1, 2], [1, 2], [1, 2]])
    )


def test_given_3d_input_when_apply_shape_into_2d_then_raises_error_if_3d():
    with pytest.raises(ValueError):
        shape_into_2d(np.array([[[1], [2]], [[3], [4]]]))


def test_when_set_random_seed_then_expect_same_random_values(preserve_random_generator_state):
    set_random_seed(0)
    numpy_vals1 = np.random.random(10)
    random_vals1 = [random.randint(0, 100) for i in range(10)]

    set_random_seed(0)
    numpy_vals2 = np.random.random(10)
    random_vals2 = [random.randint(0, 100) for i in range(10)]

    assert numpy_vals1 == approx(numpy_vals2)
    assert random_vals1 == approx(random_vals2)


def test_when_calling_setdiff2d_then_returns_expected_arrays():
    assert setdiff2d(np.array([[1, 2], [1, 4], [1, 2], [2, 3]]), np.array([[1, 4], [2, 3], [2, 4]])) == approx(
        np.array([[1, 2]])
    )
    assert setdiff2d(
        np.array([[1, 2], [1, 4], [1, 2], [2, 3]]), np.array([[1, 4], [2, 3], [2, 4]]), assume_unique=True
    ) == approx(np.array([[1, 2], [1, 2]]))
    assert setdiff2d(np.array([[1, 4], [2, 3], [2, 4]]), np.array([[1, 2], [1, 4], [1, 2], [2, 3]])) == approx(
        np.array([[2, 4]])
    )
    assert setdiff2d(np.array([[1, 2], [1, 4], [1, 2], [2, 3]]), np.array([[1, 3], [2, 5], [2, 4]])) == approx(
        np.array([[1, 2], [1, 4], [2, 3]])
    )
    assert setdiff2d(
        np.array([[1, 2], [1, 4], [1, 2], [2, 3]]), np.array([[1, 3], [2, 5], [2, 4]]), assume_unique=True
    ) == approx(np.array([[1, 2], [1, 4], [1, 2], [2, 3]]))


def test_given_non_contiguous_data_when_calling_setdiff2d_then_does_not_raise_error():
    X = np.random.normal(loc=0, scale=1, size=1000)
    Y = X + np.random.normal(loc=0, scale=1, size=1000)
    data = pd.DataFrame(data=dict(X=X, Y=Y))

    causal_model = gcm.StructuralCausalModel(nx.DiGraph([("X", "Y")]))
    gcm.auto.assign_causal_mechanisms(causal_model, data)
    gcm.fit(causal_model, data)

    generated_data = gcm.draw_samples(causal_model, num_samples=100000)

    setdiff2d(data.to_numpy(), generated_data.to_numpy())
