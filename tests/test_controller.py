# -*- coding: utf-8 -*-
"""
Tests for Controller

Tests for NanonisController and CommandRegistry.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import struct

from nanonis.command import (
    NanonisController,
    CommandRegistry,
    CommandDefinition,
    CommandEncoder,
    CommandDecoder,
)


class TestCommandRegistry:
    """Tests for CommandRegistry."""
    
    def test_empty_registry(self):
        """Test empty registry."""
        registry = CommandRegistry()
        assert len(registry) == 0
        assert registry.list_commands() == []
    
    def test_load_from_yaml(self, tmp_path):
        """Test loading from YAML file."""
        yaml_content = """
Bias.Set:
  send:
    - name: voltage
      type: float32
  recv: []
Bias.Get:
  send: []
  recv:
    - name: voltage
      type: float32
"""
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text(yaml_content)
        
        registry = CommandRegistry()
        registry.load_from_yaml(yaml_file)
        
        assert len(registry) == 2
        assert 'Bias.Set' in registry
        assert 'Bias.Get' in registry
    
    def test_get_command(self, tmp_path):
        """Test getting command definition."""
        yaml_content = """
Bias.Set:
  send:
    - name: voltage
      type: float32
  recv: []
"""
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text(yaml_content)
        
        registry = CommandRegistry()
        registry.load_from_yaml(yaml_file)
        
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
        yaml_content = """
Bias.Set:
  send: []
  recv: []
Bias.Get:
  send: []
  recv: []
Scan.Start:
  send: []
  recv: []
"""
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text(yaml_content)
        
        registry = CommandRegistry()
        registry.load_from_yaml(yaml_file)
        
        bias_cmds = registry.list_commands('Bias.')
        assert len(bias_cmds) == 2
        assert 'Bias.Set' in bias_cmds
        assert 'Bias.Get' in bias_cmds
    
    def test_list_modules(self, tmp_path):
        """Test listing modules."""
        yaml_content = """
Bias.Set:
  send: []
  recv: []
Scan.Start:
  send: []
  recv: []
ZCtrl.On:
  send: []
  recv: []
"""
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text(yaml_content)
        
        registry = CommandRegistry()
        registry.load_from_yaml(yaml_file)
        
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
        yaml_content = """
Bias.Get:
  send: []
  recv:
    - name: voltage
      type: float32
"""
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text(yaml_content)
        
        ctrl = NanonisController('127.0.0.1', 6501, yaml_file)
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
        mock_client.send_raw.return_value = struct.pack('>f', 0.5)
        mock_client_class.return_value = mock_client
        
        # Create config
        yaml_content = """
Bias.Get:
  send: []
  recv:
    - name: voltage
      type: float32
"""
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text(yaml_content)
        
        ctrl = NanonisController('127.0.0.1', 6501, yaml_file)
        ctrl.connect()
        
        result = ctrl.send('Bias.Get')
        
        mock_client.send_raw.assert_called_once_with('Bias.Get', b'')
        assert abs(result - 0.5) < 1e-6
    
    @patch('nanonis.command.controller.NanonisTCPClient')
    def test_send_command_with_args(self, mock_client_class, tmp_path):
        """Test sending command with arguments."""
        mock_client = MagicMock()
        mock_client.send_raw.return_value = b''
        mock_client_class.return_value = mock_client
        
        yaml_content = """
Bias.Set:
  send:
    - name: voltage
      type: float32
  recv: []
"""
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text(yaml_content)
        
        ctrl = NanonisController('127.0.0.1', 6501, yaml_file)
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
        
        with NanonisController('127.0.0.1', 6501) as ctrl:
            mock_client.connect.assert_called_once()
        
        mock_client.disconnect.assert_called_once()
    
    def test_list_commands(self, tmp_path):
        """Test listing available commands."""
        yaml_content = """
Bias.Set:
  send: []
  recv: []
Bias.Get:
  send: []
  recv: []
"""
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text(yaml_content)
        
        ctrl = NanonisController('127.0.0.1', 6501, yaml_file)
        commands = ctrl.list_commands()
        
        assert 'Bias.Set' in commands
        assert 'Bias.Get' in commands
    
    def test_get_command_info(self, tmp_path):
        """Test getting command info."""
        yaml_content = """
Bias.Set:
  send:
    - name: voltage
      type: float32
  recv: []
"""
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text(yaml_content)
        
        ctrl = NanonisController('127.0.0.1', 6501, yaml_file)
        info = ctrl.get_command_info('Bias.Set')
        
        assert info['name'] == 'Bias.Set'
        assert ('voltage', 'float32') in info['send_args']
        assert info['recv_args'] == []
