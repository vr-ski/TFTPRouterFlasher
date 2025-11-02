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
    logger = logging.getLogger("TFTPRouterFlasher")
    logger.setLevel(logging.DEBUG if debug_enabled else logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG if debug_enabled else logging.INFO)
    ch.setFormatter(formatter)

    fh = logging.FileHandler("TFTPRouterFlasher.log")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)

    logger.addHandler(ch)
    logger.addHandler(fh)

    return logger

def validate_interface(interface: str) -> str:
    return interface in psutil.net_if_addrs()

def get_ip_info(interface: str) -> list[str]:
    result = subprocess.run(["ip", "-4", "addr", "show", interface], capture_output=True, text=True)
    for line in result.stdout.splitlines():
        if "inet " in line:
            ip = line.strip().split()[1].split("/")[0]
            netmask = line.strip().split()[1].split("/")[1]
            return ip, netmask
    return None, None

def get_default_gateway() -> str:
    result = subprocess.run(["ip", "route"], capture_output=True, text=True)
    for line in result.stdout.splitlines():
        if line.startswith("default"):
            return line.split()[2]
    return None

def print_connection_info(hostname: str, ipaddr: str, netmask: str, gateway: str, logger: logging.Logger) -> None:
    logger.info(f"Hostname: {hostname}")
    logger.info(f"IP Address: {ipaddr}")
    logger.info(f"Netmask: {netmask}")
    logger.info(f"Gateway: {gateway}")

def ping_host(ip: str, no_ping: bool, logger: logging.Logger, retries:int = 3, delay:int =1) -> bool:
    if no_ping:
        return True

    for _ in range(retries):
        logger.info(f"Pinging IP: {ip}")
        result = subprocess.run(["ping", "-c", "1", ip], stdout=subprocess.DEVNULL)
        if result.returncode == 0:
            return True
        time.sleep(delay)
    return False

def configure_interface(interface: str, ip: str, netmask: str, gateway: str, logger: logging.Logger) -> None:
    logger.debug(f"Configuring interface {interface} with IP {ip}")
    subprocess.run(["ip", "addr", "flush", "dev", interface])
    subprocess.run(["ip", "addr", "add", f"{ip}/{netmask}", "dev", interface])
    subprocess.run(["ip", "link", "set", interface, "up"])
    subprocess.run(["ip", "route", "add", "default", "via", gateway])

def try_default_ip_range(interface: str, firmware: str, timeout: int, no_ping: bool, logger: logging.Logger) -> bool:
    for i in range(2, 26):
        test_ip = f"192.168.1.{i}"
        configure_interface(interface, test_ip, "24", "192.168.1.1", logger)
        time.sleep(2)
        if ping_host("192.168.1.1", no_ping, logger):
            return upload_binary_using_tftp("192.168.1.1", firmware, timeout, logger)
    return False

def upload_binary_using_tftp(hostname: str, firmware: str, timeout: int, logger: logging.Logger) -> bool:
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
    if not os.path.isfile(firmware):
        logger.error(f"Invalid firmware path: {firmware}")
        return False
    return True

def upload_firmware(hostname: str, interface: str, firmware: str, timeout: int, no_ping: bool, logger: logging.Logger) -> bool:
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

    return try_default_ip_range(interface, firmware, timeout, logger)

def main() -> None:
    parser = argparse.ArgumentParser(description="ASUS RT firmware rescue tool")
    parser.add_argument("--firmware", required=True, help="Path to the firmware file")
    parser.add_argument("--hostname", default="192.168.1.1", help="Router IP address")
    parser.add_argument("--timeout", type=int, default=120, help="TFTP timeout in seconds")
    parser.add_argument("--interface", default="en0", help="Network interface to use")
    parser.add_argument("--no-ping", action="store_true", help="Disable ping check. Useful on some models")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    logger = setup_logger(args.debug)

    if not validate_interface(args.interface):
        logger.error(f"Interface {args.interface} not found")
        sys.exit(1)

    if not validate_firmware_path(args.firmware, logger):
        sys.exit(1)

    if not upload_firmware(args.hostname, args.interface, args.firmware, args.timeout, args.no_ping, logger):
        logger.error("Firmware upload failed")
        sys.exit(1)

    logger.info("Firmware upload complete. Please restart your router.")

if __name__ == "__main__":
    main()
