# Inspired by arescue by Joonas Nissinen (https://github.com/jnissin/arescue)
# Original code licensed under GPL-2.0 License

import argparse
import logging
import os
import subprocess
import sys
import time

import psutil
import tftpy


def setup_logger(debug_enabled: bool) -> logging.Logger:
    """
    Configure and set up a logger with both console and file handlers.

    Args:
        debug_enabled (bool): If True, sets console log level to DEBUG, otherwise INFO.

    Returns:
        logging.Logger: Configured logger instance with console and file handlers.
    """
    logger = logging.getLogger("TFTPRouterFlasher")
    logger.setLevel(logging.DEBUG if debug_enabled else logging.INFO)

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG if debug_enabled else logging.INFO)
    ch.setFormatter(formatter)

    fh = logging.FileHandler("TFTPRouterFlasher.log")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)

    logger.addHandler(ch)
    logger.addHandler(fh)

    return logger


def validate_interface(interface: str) -> bool:
    """
    Check if the specified network interface exists on the system.

    Args:
        interface (str): Name of the network interface to validate.

    Returns:
        bool: True if interface exists, False otherwise.
    """
    return interface in psutil.net_if_addrs()


def get_ip_info(interface: str) -> tuple[str, str]:
    """
    Retrieve IP address and netmask for the specified network interface.

    Args:
        interface (str): Network interface name to query.

    Returns:
        tuple[str, str]: (IP address, netmask) or empty strings if not found.
    """
    result = subprocess.run(
        ["ip", "-4", "addr", "show", interface],
        capture_output=True,
        text=True,
    )
    for line in result.stdout.splitlines():
        if "inet " in line:
            ip = line.strip().split()[1].split("/")[0]
            netmask = line.strip().split()[1].split("/")[1]
            return ip, netmask
    return "", ""


def get_default_gateway() -> str:
    """
    Get the system's default gateway IP address.

    Returns:
        str: Default gateway IP address, or empty string if not found.
    """
    result = subprocess.run(["ip", "route"], capture_output=True, text=True)
    for line in result.stdout.splitlines():
        if line.startswith("default"):
            return line.split()[2]
    return ""


def print_connection_info(
    hostname: str,
    ipaddr: str,
    netmask: str,
    gateway: str,
    logger: logging.Logger,
) -> None:
    """
    Log network connection information for debugging and user visibility.

    Args:
        hostname (str): Target router hostname/IP.
        ipaddr (str): Local IP address.
        netmask (str): Local network mask.
        gateway (str): Default gateway.
        logger (logging.Logger): Logger instance for output.
    """
    logger.info(f"Hostname: {hostname}")
    logger.info(f"IP Address: {ipaddr}")
    logger.info(f"Netmask: {netmask}")
    logger.info(f"Gateway: {gateway}")


def ping_host(
    ip: str,
    no_ping: bool,
    logger: logging.Logger,
    retries: int = 3,
    delay: int = 1,
) -> bool:
    """
    Ping a host to check network connectivity with retry logic.

    Args:
        ip (str): IP address to ping.
        no_ping (bool): If True, skip ping and return True (for bypass mode).
        logger (logging.Logger): Logger instance for output.
        retries (int): Number of ping attempts before giving up.
        delay (int): Seconds to wait between retries.

    Returns:
        bool: True if ping successful or no_ping is True, False otherwise.
    """
    if no_ping:
        return True

    for _ in range(retries):
        logger.info(f"Pinging IP: {ip}")
        result = subprocess.run(["ping", "-c", "1", ip], stdout=subprocess.DEVNULL)
        if result.returncode == 0:
            return True
        time.sleep(delay)
    return False


def configure_interface(
    interface: str,
    ip: str,
    netmask: str,
    gateway: str,
    logger: logging.Logger,
) -> None:
    """
    Configure network interface with specified IP, netmask, and gateway.

    Args:
        interface (str): Network interface to configure.
        ip (str): IP address to assign.
        netmask (str): Network mask to apply.
        gateway (str): Default gateway to set.
        logger (logging.Logger): Logger instance for output.
    """
    logger.debug(f"Configuring interface {interface} with IP {ip}")
    subprocess.run(["ip", "addr", "flush", "dev", interface])
    subprocess.run(["ip", "addr", "add", f"{ip}/{netmask}", "dev", interface])
    subprocess.run(["ip", "link", "set", interface, "up"])
    subprocess.run(["ip", "route", "add", "default", "via", gateway])


def try_default_ip_range(
    interface: str,
    firmware: str,
    timeout: int,
    no_ping: bool,
    logger: logging.Logger,
) -> bool:
    """
    Attempt firmware upload using common default IP ranges for routers.

    This method tries IPs from 192.168.1.2 to 192.168.1.25, configuring
    the local interface and attempting TFTP upload for each.

    Args:
        interface (str): Network interface to use.
        firmware (str): Path to firmware file.
        timeout (int): TFTP timeout in seconds.
        no_ping (bool): Whether to skip ping checks.
        logger (logging.Logger): Logger instance for output.

    Returns:
        bool: True if upload successful, False if all attempts fail.
    """
    for i in range(2, 26):
        test_ip = f"192.168.1.{i}"
        configure_interface(interface, test_ip, "24", "192.168.1.1", logger)
        time.sleep(2)
        if ping_host("192.168.1.1", no_ping, logger):
            return upload_binary_using_tftp("192.168.1.1", firmware, timeout, logger)
    return False


def upload_binary_using_tftp(
    hostname: str,
    firmware: str,
    timeout: int,
    logger: logging.Logger,
) -> bool:
    """
    Upload firmware file to router using TFTP protocol.

    Args:
        hostname (str): Router IP address/hostname.
        firmware (str): Path to firmware file to upload.
        timeout (int): TFTP operation timeout in seconds.
        logger (logging.Logger): Logger instance for output.

    Returns:
        bool: True if upload successful, False on error.
    """
    logger.info(f"Uploading firmware to {hostname}")
    try:
        client = tftpy.TftpClient(hostname, 69)
        client.upload(os.path.basename(firmware), firmware, timeout=timeout)
        logger.info("Upload complete")
        return True
    except Exception as e:
        logger.error(f"TFTP upload failed: {e}")
        return False


def validate_firmware_path(firmware: str, logger: logging.Logger) -> bool:
    """
    Validate that the firmware file exists and is accessible.

    Args:
        firmware (str): Path to firmware file.
        logger (logging.Logger): Logger instance for error output.

    Returns:
        bool: True if firmware file exists, False otherwise.
    """
    if not os.path.isfile(firmware):
        logger.error(f"Invalid firmware path: {firmware}")
        return False
    return True


def upload_firmware(
    hostname: str,
    interface: str,
    firmware: str,
    timeout: int,
    no_ping: bool,
    logger: logging.Logger,
) -> bool:
    """
    Main firmware upload orchestration function.

    Attempts upload to specified hostname, falls back to default IP range
    if initial attempt fails and user approves.

    Args:
        hostname (str): Target router IP address.
        interface (str): Network interface to use.
        firmware (str): Path to firmware file.
        timeout (int): TFTP timeout in seconds.
        no_ping (bool): Whether to skip ping verification.
        logger (logging.Logger): Logger instance for output.

    Returns:
        bool: True if upload successful, False otherwise.
    """
    ipaddr, netmask = get_ip_info(interface)
    gateway = get_default_gateway()
    print_connection_info(hostname, ipaddr, netmask, gateway, logger)

    if ping_host(hostname, no_ping, logger):
        logger.info("Router is reachable")
        return upload_binary_using_tftp(hostname, firmware, timeout, logger)

    logger.warning("Router not reachable with current config")
    ans = input("Try default IP configurations? (Y/N): ").strip().lower()
    if ans != "y":
        return False

    return try_default_ip_range(interface, firmware, timeout, no_ping, logger)


def main() -> None:
    """
    Main entry point for TFTP Router Flasher application.

    Handles command line arguments, validates inputs, and orchestrates
    the firmware upload process.
    """
    parser = argparse.ArgumentParser(description="ASUS RT firmware rescue tool")
    parser.add_argument("--firmware", required=True, help="Path to the firmware file")
    parser.add_argument("--hostname", default="192.168.1.1", help="Router IP address")
    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="TFTP timeout in seconds",
    )
    parser.add_argument("--interface", default="en0", help="Network interface to use")
    parser.add_argument(
        "--no-ping",
        action="store_true",
        help="Disable ping check. Useful on some models",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    logger = setup_logger(args.debug)

    if not validate_interface(args.interface):
        logger.error(f"Interface {args.interface} not found")
        sys.exit(1)

    if not validate_firmware_path(args.firmware, logger):
        sys.exit(1)

    if not upload_firmware(
        args.hostname,
        args.interface,
        args.firmware,
        args.timeout,
        args.no_ping,
        logger,
    ):
        logger.error("Firmware upload failed")
        sys.exit(1)

    logger.info("Firmware upload complete. Please restart your router.")


if __name__ == "__main__":
    main()
