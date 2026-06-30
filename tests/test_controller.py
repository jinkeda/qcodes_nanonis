# -*- coding: utf-8 -*-
"""
Tests for Controller

Tests for NanonisController and CommandRegistry.
"""

import json
import pytest
from unittest.mock import patch, MagicMock
import struct

from nanonis.command import (
    NanonisController,
    CommandRegistry,
)


def write_command_config(tmp_path, commands):
    config_dir = tmp_path / "commands"
    config_dir.mkdir()
    (config_dir / "Test.json").write_text(json.dumps(commands), encoding="utf-8")
    return config_dir


class TestCommandRegistry:
    """Tests for CommandRegistry."""
    
    def test_empty_registry(self):
        """Test empty registry."""
        registry = CommandRegistry()
        assert len(registry) == 0
        assert registry.list_commands() == []
    
    def test_load_from_directory(self, tmp_path):
        """Test loading per-module JSON files from a directory."""
        config_dir = write_command_config(tmp_path, {
            "Bias.Set": {"args": [{"name": "Voltage", "type": "f"}], "resp": []},
            "Bias.Get": {"args": [], "resp": [{"name": "Voltage", "type": "f"}]},
        })
        registry = CommandRegistry()
        registry.load_from_dir(config_dir)
        
        assert len(registry) == 2
        assert 'Bias.Set' in registry
        assert 'Bias.Get' in registry
    
    def test_get_command(self, tmp_path):
        """Test getting command definition."""
        config_dir = write_command_config(tmp_path, {
            "Bias.Set": {"args": [{"name": "Voltage", "type": "f"}], "resp": []},
        })
        registry = CommandRegistry()
        registry.load_from_dir(config_dir)
        
        cmd = registry.get('Bias.Set')
        assert cmd.name == 'Bias.Set'
        assert len(cmd.send_args) == 1
        assert cmd.send_args[0].name == 'voltage'
        assert cmd.send_args[0].type == 'float32'
    
    def test_get_unknown_command(self):
        """Test error on unknown command."""
        registry = CommandRegistry()
        with pytest.raises(KeyError, match="Unknown command"):
            registry.get('Unknown.Command')
    
    def test_list_commands_with_prefix(self, tmp_path):
        """Test listing commands with prefix filter."""
        config_dir = write_command_config(tmp_path, {
            "Bias.Set": {"args": [], "resp": []},
            "Bias.Get": {"args": [], "resp": []},
            "Scan.Start": {"args": [], "resp": []},
        })
        registry = CommandRegistry()
        registry.load_from_dir(config_dir)
        
        bias_cmds = registry.list_commands('Bias.')
        assert len(bias_cmds) == 2
        assert 'Bias.Set' in bias_cmds
        assert 'Bias.Get' in bias_cmds
    
    def test_list_modules(self, tmp_path):
        """Test listing modules."""
        config_dir = write_command_config(tmp_path, {
            "Bias.Set": {"args": [], "resp": []},
            "Scan.Start": {"args": [], "resp": []},
            "ZCtrl.On": {"args": [], "resp": []},
        })
        registry = CommandRegistry()
        registry.load_from_dir(config_dir)
        
        modules = registry.list_modules()
        assert modules == ['Bias', 'Scan', 'ZCtrl']


class TestNanonisController:
    """Tests for NanonisController."""
    
    def test_init(self):
        """Test controller initialization."""
        ctrl = NanonisController('127.0.0.1', 6501)
        assert not ctrl.is_connected
    
    def test_init_with_config(self, tmp_path):
        """Test controller initialization with config."""
        config_dir = write_command_config(tmp_path, {
            "Bias.Get": {"args": [], "resp": [{"name": "Voltage", "type": "f"}]},
        })
        ctrl = NanonisController('127.0.0.1', 6501, config_dir)
        assert 'Bias.Get' in ctrl.list_commands()
    
    @patch('nanonis.command.controller.NanonisTCPClient')
    def test_connect_disconnect(self, mock_client_class):
        """Test connect and disconnect."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        ctrl = NanonisController('127.0.0.1', 6501)
        
        ctrl.connect()
        mock_client.connect.assert_called_once()
        
        ctrl.disconnect()
        mock_client.disconnect.assert_called_once()
    
    @patch('nanonis.command.controller.NanonisTCPClient')
    def test_send_command_no_args(self, mock_client_class, tmp_path):
        """Test sending command with no arguments."""
        # Set up mock
        mock_client = MagicMock()
        # Return encoded float32 value of 0.5
        mock_client.send_raw.return_value = (
            struct.pack('>f', 0.5) + struct.pack('>Ii', 0, 0)
        )
        mock_client_class.return_value = mock_client
        
        config_dir = write_command_config(tmp_path, {
            "Bias.Get": {"args": [], "resp": [{"name": "Voltage", "type": "f"}]},
        })
        ctrl = NanonisController('127.0.0.1', 6501, config_dir)
        ctrl.connect()
        
        result = ctrl.send('Bias.Get')
        
        mock_client.send_raw.assert_called_once_with('Bias.Get', b'')
        assert abs(result - 0.5) < 1e-6
    
    @patch('nanonis.command.controller.NanonisTCPClient')
    def test_send_command_with_args(self, mock_client_class, tmp_path):
        """Test sending command with arguments."""
        mock_client = MagicMock()
        mock_client.send_raw.return_value = struct.pack('>Ii', 0, 0)
        mock_client_class.return_value = mock_client
        
        config_dir = write_command_config(tmp_path, {
            "Bias.Set": {"args": [{"name": "Voltage", "type": "f"}], "resp": []},
        })
        ctrl = NanonisController('127.0.0.1', 6501, config_dir)
        ctrl.connect()
        
        result = ctrl.send('Bias.Set', 0.5)
        
        # Verify the encoded body
        expected_body = struct.pack('>f', 0.5)
        mock_client.send_raw.assert_called_once_with('Bias.Set', expected_body)
        assert result is None
    
    @patch('nanonis.command.controller.NanonisTCPClient')
    def test_context_manager(self, mock_client_class):
        """Test context manager usage."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        with NanonisController('127.0.0.1', 6501):
            mock_client.connect.assert_called_once()
        
        mock_client.disconnect.assert_called_once()
    
    def test_list_commands(self, tmp_path):
        """Test listing available commands."""
        config_dir = write_command_config(tmp_path, {
            "Bias.Set": {"args": [], "resp": []},
            "Bias.Get": {"args": [], "resp": []},
        })
        ctrl = NanonisController('127.0.0.1', 6501, config_dir)
        commands = ctrl.list_commands()
        
        assert 'Bias.Set' in commands
        assert 'Bias.Get' in commands
    
    def test_get_command_info(self, tmp_path):
        """Test getting command info."""
        config_dir = write_command_config(tmp_path, {
            "Bias.Set": {"args": [{"name": "Voltage", "type": "f"}], "resp": []},
        })
        ctrl = NanonisController('127.0.0.1', 6501, config_dir)
        info = ctrl.get_command_info('Bias.Set')
        
        assert info['name'] == 'Bias.Set'
        assert ('voltage', 'float32') in info['send_args']
        assert info['recv_args'] == []
