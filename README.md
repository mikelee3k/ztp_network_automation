# ZTP Network Configuration Automation

This application automates the Zero-Touch Provisioning process for network devices by fetching, validating, and deploying network configurations.

## Architecture

See the network diagram above for the system architecture. The application:
1. Fetches configurations from a cloud API
2. Validates all network settings
3. Deploys configurations to network devices
4. Logs all actions and results

## Prerequisites

- Docker

## Usage

1. Build the Docker image:
```bash
docker build -t ztp-automation .
```

2. Run the container:
```bash
docker run ztp-automation
```

## Configuration

Create a `config.json` file with the following structure:
```json
{
  "dhcp": {
    "reservations": {"00:11:22:33:44:55": "192.168.1.100"},
    "subnet": "192.168.1.0/24",
    "gateway": "192.168.1.1"
  },
  "vlans": [
    {
      "id": 10,
      "name": "Data",
      "subnet": "192.168.10.0/24"
    }
  ],
  "dns_servers": ["8.8.8.8", "8.8.4.4"],
  "firewall_rules": []
}
```

## Error Handling

The application handles:
- Invalid configuration data
- Network device connectivity issues
- API failures
- Invalid IP addresses or VLAN configurations

## Logs

Deployment logs are written to stdout and can be viewed using:
```bash
docker logs <container_id>
```
