from scripts.live_test_commands import order_commands_for_live_test


def test_module_open_commands_run_before_dependent_commands():
    commands = [
        'BiasSpectr.ChsGet',
        'AutoApproach.OnOffGet',
        'BiasSpectr.Open',
        'Bias.Get',
        'AutoApproach.Open',
    ]

    assert order_commands_for_live_test(commands) == [
        'AutoApproach.Open',
        'BiasSpectr.Open',
        'AutoApproach.OnOffGet',
        'Bias.Get',
        'BiasSpectr.ChsGet',
    ]
