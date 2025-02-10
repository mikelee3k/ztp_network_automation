# src/network_config.py

"""
Zero-Touch Provisioning (ZTP) Network Configuration Module

This module provides classes and functions for automated network device configuration.
It handles DHCP, VLAN, DNS, and firewall settings with validation and error checking.

Key components:
- DHCPConfig: Manages DHCP reservations and settings
- VLANConfig: Handles VLAN configurations
- NetworkConfig: Main class for overall network configuration
- NetworkDevice: Abstract base class for different network devices
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
import ipaddress
import json
import logging
import requests
from abc import ABC, abstractmethod

# Set up logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DHCPConfig:
    """
    DHCP configuration container with validation.
    
    Attributes:
        reservations (Dict[str, str]): MAC address to IP address mappings
        subnet (str): Network subnet in CIDR notation
        gateway (str): Gateway IP address
    """
    reservations: Dict[str, str]
    subnet: str
    gateway: str

    def validate(self) -> bool:
        """
        Validates DHCP configuration components.
        
        Returns:
            bool: True if all components are valid, False otherwise
        """
        try:
            # Validate subnet and gateway addresses
            ipaddress.ip_network(self.subnet)
            ipaddress.ip_address(self.gateway)
            
            # Check each MAC address reservation
            for mac, ip in self.reservations.items():
                if not self._is_valid_mac(mac):
                    logger.error(f"Invalid MAC address format: {mac}")
                    return False
                ipaddress.ip_address(ip)
            return True
        except ValueError as e:
            logger.error(f"DHCP validation error: {e}")
            return False

    @staticmethod
    def _is_valid_mac(mac: str) -> bool:
        """
        Validates MAC address format.
        
        Args:
            mac (str): MAC address to validate
            
        Returns:
            bool: True if MAC address format is valid
        """
        if len(mac.split(':')) != 6:
            return False
        try:
            int(mac.replace(':', ''), 16)
            return True
        except ValueError:
            return False

@dataclass
class VLANConfig:
    """
    VLAN configuration container with validation.
    
    Attributes:
        id (int): VLAN ID (1-4094)
        name (str): VLAN name
        subnet (str): VLAN subnet in CIDR notation
    """
    id: int
    name: str
    subnet: str

    def validate(self) -> bool:
        """
        Validates VLAN configuration.
        
        Checks:
        - VLAN ID is within valid range (1-4094)
        - Subnet is valid CIDR notation
        
        Returns:
            bool: True if configuration is valid
        """
        try:
            if not (1 <= self.id <= 4094):
                logger.error(f"Invalid VLAN ID: {self.id}")
                return False
            ipaddress.ip_network(self.subnet)
            return True
        except ValueError as e:
            logger.error(f"VLAN validation error: {e}")
            return False

class NetworkConfig:
    """
    Main network configuration container class.
    
    Handles overall network configuration including:
    - DHCP settings
    - VLAN configurations
    - DNS servers
    - Firewall rules
    """
    def __init__(self):
        self.dhcp: Optional[DHCPConfig] = None
        self.vlans: List[VLANConfig] = []
        self.dns_servers: List[str] = []
        self.firewall_rules: List[Dict] = []

    def validate(self) -> bool:
        """
        Validates entire network configuration.
        
        Checks:
        - DHCP configuration validity
        - VLAN configuration validity
        - No duplicate VLAN IDs
        - Valid DNS server IP addresses
        
        Returns:
            bool: True if all configurations are valid
        """
        try:
            # Validate DHCP configuration if present
            if self.dhcp and not self.dhcp.validate():
                return False
            
            # Validate all VLAN configurations
            for vlan in self.vlans:
                if not vlan.validate():
                    return False
            
            # Check for duplicate VLAN IDs
            vlan_ids = [v.id for v in self.vlans]
            if len(vlan_ids) != len(set(vlan_ids)):
                logger.error("Duplicate VLAN IDs detected")
                return False
            
            # Validate DNS server IP addresses
            for dns in self.dns_servers:
                ipaddress.ip_address(dns)
                
            return True
        except ValueError as e:
            logger.error(f"Network configuration validation error: {e}")
            return False

    @classmethod
    def from_json(cls, config_data: dict) -> 'NetworkConfig':
        """
        Creates NetworkConfig instance from JSON data.
        
        Args:
            config_data (dict): JSON configuration data
            
        Returns:
            NetworkConfig: Initialized configuration object
            
        Raises:
            ValueError: If configuration data is invalid
        """
        config = cls()
        
        # Parse DHCP configuration if present
        if 'dhcp' in config_data:
            config.dhcp = DHCPConfig(**config_data['dhcp'])
            
        # Parse VLAN configurations
        if 'vlans' in config_data:
            config.vlans = [VLANConfig(**vlan) for vlan in config_data['vlans']]
            
        # Parse DNS and firewall configurations
        config.dns_servers = config_data.get('dns_servers', [])
        config.firewall_rules = config_data.get('firewall_rules', [])
        
        if not config.validate():
            raise ValueError("Invalid configuration data")
            
        return config

class NetworkDevice(ABC):
    """
    Abstract base class for network devices.
    
    Provides common interface for all network devices (routers, switches, etc.)
    """
    def __init__(self, hostname: str, ip: str):
        self.hostname = hostname
        self.ip = ip

    @abstractmethod
    def deploy_config(self, config: NetworkConfig) -> bool:
        """
        Deploy configuration to device.
        
        Args:
            config (NetworkConfig): Configuration to deploy
            
        Returns:
            bool: True if deployment successful
        """
        pass

class Router(NetworkDevice):
    """Router device implementation."""
    def deploy_config(self, config: NetworkConfig) -> bool:
        """
        Deploy configuration to router.
        
        Simulates:
        - DHCP configuration
        - Firewall rules application
        """
        logger.info(f"Deploying configuration to router {self.hostname}")
        
        if config.dhcp:
            logger.info(f"Configuring DHCP on {self.hostname}")
        if config.firewall_rules:
            logger.info(f"Applying firewall rules on {self.hostname}")
        return True

class Switch(NetworkDevice):
    """Switch device implementation."""
    def deploy_config(self, config: NetworkConfig) -> bool:
        """
        Deploy configuration to switch.
        
        Simulates:
        - VLAN configuration
        """
        logger.info(f"Deploying configuration to switch {self.hostname}")
        
        for vlan in config.vlans:
            logger.info(f"Configuring VLAN {vlan.id} on {self.hostname}")
        return True

def fetch_config(api_url: str) -> dict:
    """
    Fetch configuration from API server.
    
    Args:
        api_url (str): URL of configuration API
        
    Returns:
        dict: Configuration data
        
    Raises:
        requests.exceptions.RequestException: If API call fails
    """
    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch configuration: {e}")
        raise

def deploy_configuration(config: NetworkConfig, devices: List[NetworkDevice]) -> bool:
    """
    Deploy configuration to all network devices.
    
    Args:
        config (NetworkConfig): Configuration to deploy
        devices (List[NetworkDevice]): List of target devices
        
    Returns:
        bool: True if deployment successful on all devices
    """
    success = True
    for device in devices:
        try:
            if not device.deploy_config(config):
                success = False
                logger.error(f"Failed to deploy config to {device.hostname}")
        except Exception as e:
            success = False
            logger.error(f"Error deploying config to {device.hostname}: {e}")
    return success

# Example usage
if __name__ == "__main__":
    # Simulate API response with local file
    with open("config.json", "r") as f:
        config_data = json.load(f)
    
    try:
        # Initialize and deploy configuration
        network_config = NetworkConfig.from_json(config_data)
        devices = [
            Router("router1", "192.168.1.1"),
            Switch("switch1", "192.168.1.2")
        ]
        deploy_configuration(network_config, devices)
    except Exception as e:
        logger.error(f"Configuration deployment failed: {e}")
