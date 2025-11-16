import logging
import subprocess
from unittest.mock import Mock, call, patch

import pytest

# Import the module under test
from tftp_router_flasher.main import (
    configure_interface,
    get_default_gateway,
    get_ip_info,
    main,
    ping_host,
    print_connection_info,
    setup_logger,
    try_default_ip_range,
    upload_binary_using_tftp,
    upload_firmware,
    validate_firmware_path,
    validate_interface,
)


class TestSetupLogger:
    def setup_method(self):
        """Run before each test method."""
        self.logger = logging.getLogger("TFTPRouterFlasher")
        self.original_handlers = self.logger.handlers[:]
        # Clear all handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)

    def teardown_method(self):
        """Run after each test method."""
        # Restore original state
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        for handler in self.original_handlers:
            self.logger.addHandler(handler)

    def test_setup_logger_debug_enabled(self):
        logger = setup_logger(debug_enabled=True)
        assert logger.level == logging.DEBUG
        assert len(logger.handlers) == 2

    def test_setup_logger_debug_disabled(self):
        logger = setup_logger(debug_enabled=False)
        assert logger.level == logging.INFO
        assert len(logger.handlers) == 2


class TestValidateInterface:
    def setup_method(self):
        """Run before each test method."""
        pass  # No setup needed for this class

    def teardown_method(self):
        """Run after each test method."""
        pass  # No teardown needed for this class

    @patch("tftp_router_flasher.main.psutil.net_if_addrs")
    def test_validate_interface_exists(self, mock_if_addrs):
        mock_if_addrs.return_value = {"eth0": "mock", "wlan0": "mock"}
        assert validate_interface("eth0") is True

    @patch("tftp_router_flasher.main.psutil.net_if_addrs")
    def test_validate_interface_not_exists(self, mock_if_addrs):
        mock_if_addrs.return_value = {"eth0": "mock", "wlan0": "mock"}
        assert validate_interface("nonexistent") is False


class TestGetIPInfo:
    def setup_method(self):
        """Run before each test method."""
        pass

    def teardown_method(self):
        """Run after each test method."""
        pass

    @patch("tftp_router_flasher.main.subprocess.run")
    def test_get_ip_info_success(self, mock_run):
        mock_output = "2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000\n    inet 192.168.1.10/24 brd 192.168.1.255 scope global eth0"
        mock_run.return_value = Mock(stdout=mock_output, returncode=0)

        ip, netmask = get_ip_info("eth0")
        assert ip == "192.168.1.10"
        assert netmask == "24"

    @patch("tftp_router_flasher.main.subprocess.run")
    def test_get_ip_info_no_inet(self, mock_run):
        mock_output = "2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000"
        mock_run.return_value = Mock(stdout=mock_output, returncode=0)

        ip, netmask = get_ip_info("eth0")
        assert ip == ""
        assert netmask == ""


class TestGetDefaultGateway:
    def setup_method(self):
        """Run before each test method."""
        pass

    def teardown_method(self):
        """Run after each test method."""
        pass

    @patch("tftp_router_flasher.main.subprocess.run")
    def test_get_default_gateway_found(self, mock_run):
        mock_output = "default via 192.168.1.1 dev eth0 proto static"
        mock_run.return_value = Mock(stdout=mock_output, returncode=0)

        gateway = get_default_gateway()
        assert gateway == "192.168.1.1"

    @patch("tftp_router_flasher.main.subprocess.run")
    def test_get_default_gateway_not_found(self, mock_run):
        mock_output = "192.168.1.0/24 dev eth0 proto kernel scope link src 192.168.1.10"
        mock_run.return_value = Mock(stdout=mock_output, returncode=0)

        gateway = get_default_gateway()
        assert gateway == ""


class TestPrintConnectionInfo:
    def setup_method(self):
        """Run before each test method."""
        pass

    def teardown_method(self):
        """Run after each test method."""
        pass

    def test_print_connection_info(self, caplog):
        logger = logging.getLogger("test")
        with caplog.at_level(logging.INFO):
            print_connection_info(
                "router.local", "192.168.1.10", "24", "192.168.1.1", logger
            )

        assert "Hostname: router.local" in caplog.text
        assert "IP Address: 192.168.1.10" in caplog.text
        assert "Netmask: 24" in caplog.text
        assert "Gateway: 192.168.1.1" in caplog.text


class TestPingHost:
    def setup_method(self):
        """Run before each test method."""
        pass

    def teardown_method(self):
        """Run after each test method."""
        pass

    @patch("tftp_router_flasher.main.subprocess.run")
    def test_ping_host_success(self, mock_run):
        mock_run.return_value = Mock(returncode=0)
        logger = Mock()

        result = ping_host("192.168.1.1", False, logger)
        assert result is True
        mock_run.assert_called_once_with(
            ["ping", "-c", "1", "192.168.1.1"], stdout=subprocess.DEVNULL
        )

    @patch("tftp_router_flasher.main.subprocess.run")
    def test_ping_host_failure(self, mock_run):
        mock_run.return_value = Mock(returncode=1)
        logger = Mock()

        result = ping_host("192.168.1.1", False, logger)
        assert result is False

    @patch("tftp_router_flasher.main.subprocess.run")
    def test_ping_host_no_ping(self, mock_run):
        logger = Mock()

        result = ping_host("192.168.1.1", True, logger)
        assert result is True
        mock_run.assert_not_called()


class TestConfigureInterface:
    def setup_method(self):
        """Run before each test method."""
        pass

    def teardown_method(self):
        """Run after each test method."""
        pass

    @patch("tftp_router_flasher.main.subprocess.run")
    def test_configure_interface(self, mock_run):
        logger = Mock()

        configure_interface("eth0", "192.168.1.10", "24", "192.168.1.1", logger)

        expected_calls = [
            call(["ip", "addr", "flush", "dev", "eth0"]),
            call(["ip", "addr", "add", "192.168.1.10/24", "dev", "eth0"]),
            call(["ip", "link", "set", "eth0", "up"]),
            call(["ip", "route", "add", "default", "via", "192.168.1.1"]),
        ]
        mock_run.assert_has_calls(expected_calls)


class TestUploadBinaryUsingTFTP:
    def setup_method(self):
        """Run before each test method."""
        pass

    def teardown_method(self):
        """Run after each test method."""
        pass

    @patch("tftp_router_flasher.main.tftpy.TftpClient")
    def test_upload_binary_success(self, mock_tftp_client):
        mock_client = Mock()
        mock_tftp_client.return_value = mock_client
        logger = Mock()

        result = upload_binary_using_tftp(
            "192.168.1.1", "/path/to/firmware.bin", 120, logger
        )

        assert result is True
        mock_tftp_client.assert_called_once_with("192.168.1.1", 69)
        mock_client.upload.assert_called_once_with(
            "firmware.bin", "/path/to/firmware.bin", timeout=120
        )

    @patch("tftp_router_flasher.main.tftpy.TftpClient")
    def test_upload_binary_failure(self, mock_tftp_client):
        mock_tftp_client.side_effect = Exception("Connection failed")
        logger = Mock()

        result = upload_binary_using_tftp(
            "192.168.1.1", "/path/to/firmware.bin", 120, logger
        )

        assert result is False
        logger.error.assert_called_once_with("TFTP upload failed: Connection failed")


class TestValidateFirmwarePath:
    def setup_method(self):
        """Run before each test method."""
        pass

    def teardown_method(self):
        """Run after each test method."""
        pass

    @patch("tftp_router_flasher.main.os.path.isfile")
    def test_validate_firmware_path_exists(self, mock_isfile):
        mock_isfile.return_value = True
        logger = Mock()

        result = validate_firmware_path("/path/to/firmware.bin", logger)
        assert result is True

    @patch("tftp_router_flasher.main.os.path.isfile")
    def test_validate_firmware_path_not_exists(self, mock_isfile):
        mock_isfile.return_value = False
        logger = Mock()

        result = validate_firmware_path("/path/to/firmware.bin", logger)
        assert result is False
        logger.error.assert_called_once_with(
            "Invalid firmware path: /path/to/firmware.bin"
        )


class TestTryDefaultIPRange:
    def setup_method(self):
        """Run before each test method."""
        pass

    def teardown_method(self):
        """Run after each test method."""
        pass

    @patch("tftp_router_flasher.main.upload_binary_using_tftp")
    @patch("tftp_router_flasher.main.ping_host")
    @patch("tftp_router_flasher.main.configure_interface")
    @patch("tftp_router_flasher.main.time.sleep")
    def test_try_default_ip_range_success(
        self, mock_sleep, mock_configure, mock_ping, mock_upload
    ):
        mock_ping.return_value = True
        mock_upload.return_value = True
        logger = Mock()

        result = try_default_ip_range("eth0", "/firmware.bin", 120, False, logger)

        assert result is True
        mock_configure.assert_called()
        mock_ping.assert_called_with("192.168.1.1", False, logger)
        mock_upload.assert_called_once_with("192.168.1.1", "/firmware.bin", 120, logger)

    @patch("tftp_router_flasher.main.upload_binary_using_tftp")
    @patch("tftp_router_flasher.main.ping_host")
    @patch("tftp_router_flasher.main.configure_interface")
    @patch("tftp_router_flasher.main.time.sleep")
    def test_try_default_ip_range_failure(
        self, mock_sleep, mock_configure, mock_ping, mock_upload
    ):
        mock_ping.return_value = False  # No router responds
        logger = Mock()

        result = try_default_ip_range("eth0", "/firmware.bin", 120, False, logger)

        assert result is False
        assert mock_configure.call_count == 24  # Tries all 24 IPs
        mock_upload.assert_not_called()


class TestUploadFirmware:
    def setup_method(self):
        """Run before each test method."""
        pass

    def teardown_method(self):
        """Run after each test method."""
        pass

    @patch("tftp_router_flasher.main.upload_binary_using_tftp")
    @patch("tftp_router_flasher.main.ping_host")
    @patch("tftp_router_flasher.main.get_default_gateway")
    @patch("tftp_router_flasher.main.get_ip_info")
    @patch("tftp_router_flasher.main.print_connection_info")
    def test_upload_firmware_direct_success(
        self, mock_print, mock_get_ip, mock_get_gw, mock_ping, mock_upload
    ):
        mock_get_ip.return_value = ("192.168.1.10", "24")
        mock_get_gw.return_value = "192.168.1.1"
        mock_ping.return_value = True
        mock_upload.return_value = True
        logger = Mock()

        result = upload_firmware(
            "192.168.1.1", "eth0", "/firmware.bin", 120, False, logger
        )

        assert result is True
        mock_ping.assert_called_once_with("192.168.1.1", False, logger)
        mock_upload.assert_called_once_with("192.168.1.1", "/firmware.bin", 120, logger)

    @patch("builtins.input")  # Changed from tftp_router_flasher.main.builtins.input
    @patch("tftp_router_flasher.main.try_default_ip_range")
    @patch("tftp_router_flasher.main.ping_host")
    @patch("tftp_router_flasher.main.get_default_gateway")
    @patch("tftp_router_flasher.main.get_ip_info")
    @patch("tftp_router_flasher.main.print_connection_info")  # Added this mock
    def test_upload_firmware_fallback_success(
        self,
        mock_print,
        mock_get_ip,
        mock_get_gw,
        mock_ping,
        mock_try_range,
        mock_input,
    ):
        mock_get_ip.return_value = ("192.168.1.10", "24")
        mock_get_gw.return_value = "192.168.1.1"
        mock_ping.return_value = False  # Router not reachable initially
        mock_input.return_value = "y"  # User agrees to try default range
        mock_try_range.return_value = True  # Fallback succeeds
        logger = Mock()

        result = upload_firmware(
            "192.168.1.1", "eth0", "/firmware.bin", 120, False, logger
        )

        assert result is True
        mock_try_range.assert_called_once_with(
            "eth0", "/firmware.bin", 120, False, logger
        )

    @patch("builtins.input")  # Changed from tftp_router_flasher.main.builtins.input
    @patch("tftp_router_flasher.main.try_default_ip_range")
    @patch("tftp_router_flasher.main.ping_host")
    @patch("tftp_router_flasher.main.get_default_gateway")
    @patch("tftp_router_flasher.main.get_ip_info")
    @patch("tftp_router_flasher.main.print_connection_info")  # Added this mock
    def test_upload_firmware_user_declines_fallback(
        self,
        mock_print,
        mock_get_ip,
        mock_get_gw,
        mock_ping,
        mock_try_range,
        mock_input,
    ):
        mock_get_ip.return_value = ("192.168.1.10", "24")
        mock_get_gw.return_value = "192.168.1.1"
        mock_ping.return_value = False
        mock_input.return_value = "n"  # User declines fallback
        logger = Mock()

        result = upload_firmware(
            "192.168.1.1", "eth0", "/firmware.bin", 120, False, logger
        )

        assert result is False
        mock_try_range.assert_not_called()


class TestMain:
    def setup_method(self):
        """Run before each test method."""
        pass

    def teardown_method(self):
        """Run after each test method."""
        pass

    @patch("tftp_router_flasher.main.upload_firmware")
    @patch("tftp_router_flasher.main.validate_firmware_path")
    @patch("tftp_router_flasher.main.validate_interface")
    @patch("tftp_router_flasher.main.setup_logger")
    @patch("tftp_router_flasher.main.sys.exit")
    def test_main_success(
        self,
        mock_exit,
        mock_setup_logger,
        mock_validate_interface,
        mock_validate_firmware,
        mock_upload,
    ):
        mock_setup_logger.return_value = Mock()
        mock_validate_interface.return_value = True
        mock_validate_firmware.return_value = True
        mock_upload.return_value = True

        test_args = [
            "tftp_router_flasher.py",
            "--firmware",
            "/firmware.bin",
            "--hostname",
            "192.168.1.1",
            "--interface",
            "eth0",
        ]

        with patch("sys.argv", test_args):
            main()

        mock_upload.assert_called_once()
        mock_exit.assert_not_called()

    @patch("tftp_router_flasher.main.upload_firmware")
    @patch("tftp_router_flasher.main.validate_firmware_path")
    @patch("tftp_router_flasher.main.validate_interface")
    @patch("tftp_router_flasher.main.setup_logger")
    def test_main_invalid_interface(
        self,
        mock_setup_logger,
        mock_validate_interface,
        mock_validate_firmware,
        mock_upload,
    ):
        mock_setup_logger.return_value = Mock()
        mock_validate_interface.return_value = False
        mock_validate_firmware.return_value = True

        test_args = [
            "tftp_router_flasher.py",
            "--firmware",
            "/firmware.bin",
            "--interface",
            "invalid_interface",
        ]

        with patch("sys.argv", test_args):
            with pytest.raises(SystemExit) as exc_info:
                main()

        # Check that it exited with code 1
        assert exc_info.value.code == 1
        mock_upload.assert_not_called()

    @patch("tftp_router_flasher.main.upload_firmware")
    @patch("tftp_router_flasher.main.validate_firmware_path")
    @patch("tftp_router_flasher.main.validate_interface")
    @patch("tftp_router_flasher.main.setup_logger")
    def test_main_invalid_firmware(
        self,
        mock_setup_logger,
        mock_validate_interface,
        mock_validate_firmware,
        mock_upload,
    ):
        mock_setup_logger.return_value = Mock()
        mock_validate_interface.return_value = True
        mock_validate_firmware.return_value = False

        test_args = [
            "tftp_router_flasher.py",
            "--firmware",
            "/nonexistent.bin",
            "--interface",
            "eth0",
        ]

        with patch("sys.argv", test_args):
            with pytest.raises(SystemExit) as exc_info:
                main()

        # Check that it exited with code 1
        assert exc_info.value.code == 1
        mock_upload.assert_not_called()

    @patch("tftp_router_flasher.main.upload_firmware")
    @patch("tftp_router_flasher.main.validate_firmware_path")
    @patch("tftp_router_flasher.main.validate_interface")
    @patch("tftp_router_flasher.main.setup_logger")
    def test_main_upload_failed(
        self,
        mock_setup_logger,
        mock_validate_interface,
        mock_validate_firmware,
        mock_upload,
    ):
        mock_setup_logger.return_value = Mock()
        mock_validate_interface.return_value = True
        mock_validate_firmware.return_value = True
        mock_upload.return_value = False

        test_args = [
            "tftp_router_flasher.py",
            "--firmware",
            "/firmware.bin",
            "--interface",
            "eth0",
        ]

        with patch("sys.argv", test_args):
            with pytest.raises(SystemExit) as exc_info:
                main()

        # Check that it exited with code 1
        assert exc_info.value.code == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
