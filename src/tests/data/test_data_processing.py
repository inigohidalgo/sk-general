import pytest
from skgen.data import data_processing


class TestHelpers:
    @pytest.mark.skip(reason="Not implemented")
    def test_is_true(self):
        assert False

    @pytest.mark.skip(reason="Not implemented")
    def test_index_pattern_mask(self):
        assert False

    @pytest.mark.skip(reason="Not implemented")
    def test_extract_target_from_df(self):
        assert False

    def test_iter_to_dict_default(self):

        # test_handler = data_processing.DataHandler(input_type="iter", output_type="dict")

        input_data = [1, 2]
        output_data = data_processing.iter_to_dict(input_data)
        # output_data = test_handler(input_data)
        expected_output_data = {0: 1, 1: 2}
        assert output_data == expected_output_data

    def test_iter_to_dict_item_as_keys(self):
        input_data = [("X", "y"), 1, 2]
        output_data = data_processing.iter_to_dict(input_data, index_as_keys=False)
        expected_output_data = {"X": 1, "y": 2}
        assert output_data == expected_output_data

    def test_iter_to_dict_with_keys(self):
        input_data = [1, 2]
        output_data = data_processing.iter_to_dict(input_data, keys=["X", "y"])
        expected_output_data = {"X": 1, "y": 2}
        assert output_data == expected_output_data

    def test_dict_to_iter_default(self):
        input_data = {"X": 1, "y": 2}
        output_data = data_processing.dict_to_iter(input_data)
        expected_output_data = [1, 2]
        assert output_data == expected_output_data

    def test_dict_to_iter_prepend_keys(self):
        input_data = {"X": 1, "y": 2}
        output_data = data_processing.dict_to_iter(input_data, prepend_keys=True)
        expected_output_data = [("X", "y"), 1, 2]
        assert output_data == expected_output_data


class TestDataHandler:
    def test_receive_data(self):
        test_handler = data_processing.DataHandler(input_type="iter")
        input_data = [1, 2]
        test_handler.receive_data(input_data)
        assert (
            test_handler.data == input_data
            and test_handler.data_status.current_type == "iter"
        )

    @pytest.mark.parametrize(
        "input_type, input",
        (
            ("iter", {"a": "b"}),  # TODO: dict passing for iterable? may be right
            ("iter", 3),
            ("dict", [1, 2]),
        ),
    )
    def test_receive_wrong_data(self, input_type, input):
        # todo: single test to make sure function is receiving data right
        # and extract rest of tests to only test each verifier
        test_handler = data_processing.DataHandler(input_type=input_type)
        with pytest.raises(TypeError):
            test_handler.receive_data(input)

    def test_convert_data(self):
        input_data = [1, 2]
        test_handler = data_processing.DataHandler(
            input_type="iter", output_type="dict"
        )
        output_data = test_handler(input_data)
        expected_output_data = {0: 1, 1: 2}
        assert output_data == expected_output_data
