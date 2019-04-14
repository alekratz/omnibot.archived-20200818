import os
import tempfile
import pytest
from omnibot.config import *


def test_empty_config():
    cfg = config_from_ucl("")
    assert len(cfg) == 0


def test_server_config():
    cfg = config_from_ucl("""
server {
    "irc1.example.com" {
    	nick = "test1"
    }

    "irc2" {
	address = "irc2.example.com"
    	nick = "test2"
    	port = 6668
    }

    "irc3" {
	address = "irc3.example.com"
    	nick = "test3"
    	ssl = true
    }

    "irc4.example.com" {
    	nick = "test4"
    	port = 6697
    }

    "irc5.example.com" {
    	nick = "test5"
    	port = 6687
    	ssl = true
    }
}""")
    assert len(cfg) == 5

    assert cfg[0].address == 'irc1.example.com'
    assert cfg[0].nick == 'test1'
    assert cfg[0].port == 6667
    assert cfg[0].ssl == False
    assert cfg[0].modules == {}

    assert cfg[1].address == 'irc2.example.com'
    assert cfg[1].nick == 'test2'
    assert cfg[1].port == 6668
    assert cfg[1].ssl == False
    assert cfg[1].modules == {}

    assert cfg[2].address == 'irc3.example.com'
    assert cfg[2].nick == 'test3'
    assert cfg[2].port == 6697
    assert cfg[2].ssl == True
    assert cfg[2].modules == {}

    assert cfg[3].address == 'irc4.example.com'
    assert cfg[3].nick == 'test4'
    assert cfg[3].port == 6697
    assert cfg[3].ssl == False
    assert cfg[3].modules == {}

    assert cfg[4].address == 'irc5.example.com'
    assert cfg[4].nick == 'test5'
    assert cfg[4].port == 6687
    assert cfg[4].ssl == True
    assert cfg[4].modules == {}


def test_module_config():
    cfg = config_from_ucl("""
server "irc.example.com" {
    nick = "test"
    modules {
        nickserv {}
        rtd {
            channels = ["#test1", "#test2"]
            args { max_sides = 100 }
        }
    }
}""")
    assert len(cfg) == 1
    cfg = cfg[0]
    assert cfg.address == 'irc.example.com'
    assert cfg.nick == 'test'
    assert len(cfg.modules) == 2
    assert 'nickserv' in cfg.modules
    assert 'rtd' in cfg.modules
    assert len(cfg.modules['nickserv'].channels) == 0
    assert len(cfg.modules['nickserv'].args) == 0
    rtd = cfg.modules['rtd']
    assert len(rtd.channels) == 2
    assert set(rtd.channels) == {'#test1', '#test2'}
    assert len(rtd.args) == 1
    assert rtd.args['max_sides'] == 100
