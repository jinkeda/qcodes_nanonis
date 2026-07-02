from scripts.live_test_commands import (
    PASS,
    order_commands_for_live_test,
    paired_getter_name,
    roundtrip_args,
)


def test_commands_group_by_module_and_defer_starts():
    commands = [
        'BiasSpectr.ChsGet',
        'BiasSpectr.Start',
        'BiasSpectr.ChsSet',
        'BiasSpectr.Stop',
        'AutoApproach.OnOffGet',
        'BiasSpectr.Open',
        'Bias.Get',
        'AutoApproach.Open',
    ]

    assert order_commands_for_live_test(commands) == [
        'AutoApproach.Open',
        'AutoApproach.OnOffGet',
        'Bias.Get',
        'BiasSpectr.Open',
        'BiasSpectr.ChsGet',
        'BiasSpectr.ChsSet',
        'BiasSpectr.Stop',
        'BiasSpectr.Start',
    ]


def test_setter_uses_exact_fields_from_matching_getter():
    getter = {
        'category': PASS,
        'decoded': {'num_channels': 2, 'channel_indexes': [0, 3]},
        'decoded_types': [
            ('num_channels', 'int32'),
            ('channel_indexes', 'array_int32'),
        ],
    }

    assert paired_getter_name('TCPLog.ChsSet') == 'TCPLog.ChsGet'
    assert roundtrip_args(
        [('num_channels', 'int32'), ('channel_indexes', 'array_int32')],
        getter,
    ) == (2, [0, 3])


def test_setter_does_not_guess_when_getter_fields_differ():
    getter = {
        'category': PASS,
        'decoded': {'status': 1},
        'decoded_types': [('status', 'uint32')],
    }

    assert roundtrip_args([('on_off', 'uint32')], getter) is None


def test_setter_does_not_reuse_same_named_field_with_different_wire_type():
    getter = {
        'category': PASS,
        'decoded': {'additional_rt_signal_1': '- no signal -'},
        'decoded_types': [('additional_rt_signal_1', 'string')],
    }

    assert roundtrip_args(
        [('additional_rt_signal_1', 'int32')], getter
    ) is None


def test_setter_reuses_compatible_fields_and_synthesizes_extra_controls():
    getter = {
        'category': PASS,
        'decoded': {'x_m': 1.5e-9, 'y_m': -2.5e-9},
        'decoded_types': [('x_m', 'float64'), ('y_m', 'float64')],
    }

    assert roundtrip_args(
        [
            ('x_m', 'float64'),
            ('y_m', 'float64'),
            ('wait_end_of_move', 'uint32'),
        ],
        getter,
    ) == (1.5e-9, -2.5e-9, 0)
