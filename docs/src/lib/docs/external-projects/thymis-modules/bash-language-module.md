# Using the Bash language module

The **Bash Language Module** for Thymis allows you to write and run bash scripts on your devices directly from the Thymis UI — including package dependencies, service setup, and timer configuration — without dropping into a custom Nix expression.

## How to Use the Bash Module

1. **Add the module**: In your device or tag configuration, add the "Bash Module" from the module list.

2. **Configure your script**: Write your bash code directly in the "Bash Script" field.

3. **Set dependencies**: Add any required packages from nixpkgs (e.g., `curl`, `jq`, `git`).

4. **Configure timing**: Use the timer configuration to control when and how often your script runs.

## Module Settings

| Setting | Type | Purpose |
|---------|------|---------|
| **Timer Configuration** | SystemdTimer | Controls when the script runs (oneshot, recurring, etc.) |
| **Required Packages** | List | System packages from nixpkgs to include in PATH |
| **Bash Script** | Code | The bash script to execute |

## Example: System Status Logger

Here's an example that logs system status information every 5 minutes:

```bash
# Configuration
LOG_FILE="/var/log/system-status.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Create log entry
echo "=== System Status at $TIMESTAMP ===" >> "$LOG_FILE"

# Log disk usage
echo "Disk Usage:" >> "$LOG_FILE"
df -h / >> "$LOG_FILE"

# Log memory usage
echo "Memory Usage:" >> "$LOG_FILE"
free -h >> "$LOG_FILE"

# Log system load
echo "System Load:" >> "$LOG_FILE"
uptime >> "$LOG_FILE"

# Log network interfaces
echo "Network Interfaces:" >> "$LOG_FILE"
ip addr show >> "$LOG_FILE"

echo "" >> "$LOG_FILE"

# Optional: Send status to remote server
if command -v curl &> /dev/null; then
    STATUS_DATA=$(cat << EOF
{
    "timestamp": "$TIMESTAMP",
    "hostname": "$(hostname)",
    "uptime": "$(uptime)",
    "disk_usage": "$(df -h / | tail -1)",
    "memory": "$(free -h | grep Mem)"
}
EOF
)

    # Uncomment to send to monitoring service
    # curl -X POST https://your-monitoring-service.com/api/status \
    #      -H "Content-Type: application/json" \
    #      -d "$STATUS_DATA"
fi

echo "System status logged at $TIMESTAMP"
```

### Configuration for the Example

- **Required Packages**: Add `curl`, `jq` if you need JSON processing, or other tools your script uses
- **Timer Configuration**: Set to run every 5 minutes using systemd timer
- **Bash Script**: The script above

## Example: Simple Backup Script

Here's another example that creates backups of important directories:

```bash
# Configuration
SOURCE_DIR="/home/user/important-data"
BACKUP_DIR="/backup"
DATE=$(date '+%Y%m%d_%H%M%S')
BACKUP_NAME="backup_$DATE.tar.gz"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Create backup
echo "Starting backup at $(date)"
if tar -czf "$BACKUP_DIR/$BACKUP_NAME" -C "$SOURCE_DIR" .; then
    echo "Backup completed successfully: $BACKUP_DIR/$BACKUP_NAME"

    # Clean up old backups (keep only last 7)
    cd "$BACKUP_DIR" && ls -t backup_*.tar.gz | tail -n +8 | xargs rm -f
    echo "Cleaned up old backups"
else
    echo "Backup failed!" >&2
    exit 1
fi

# Log backup size
BACKUP_SIZE=$(du -h "$BACKUP_DIR/$BACKUP_NAME" | cut -f1)
echo "Backup size: $BACKUP_SIZE"
```

## Benefits

The Bash Module provides several advantages:

- **Familiar**: Use standard bash scripting without Nix knowledge
- **Package management**: Easy access to nixpkgs tools
- **Service integration**: Automatic systemd service generation
- **Timer support**: Built-in scheduling capabilities
- **System integration**: Full access to system commands and utilities

## Common Use Cases

- **System monitoring**: Log system metrics, check service status
- **Data backup**: Create and manage backups of important files
- **Log processing**: Parse and analyze log files
- **Network tasks**: API calls, file downloads, system updates
- **Maintenance**: Cleanup tasks, disk space management

## Best Practices

1. **Error handling**: Always check command exit codes and handle errors appropriately
2. **Logging**: Use proper logging to track script execution
3. **Permissions**: Be mindful of file permissions and user context
4. **Dependencies**: Only include packages you actually need
5. **Security**: Be cautious with user input and external data

## Timer Configuration

The timer configuration supports various systemd timer options:

- **OnCalendar**: Run on specific calendar events (daily, weekly, etc.)
- **OnBootSec**: Run after system boot
- **OnUnitActiveSec**: Run repeatedly with intervals
- **Persistent**: Catch up on missed runs after system downtime

## Migration from Custom Nix

If you have existing bash scripts in a Custom Nix Module, you can easily migrate:

1. Copy your bash script to the "Bash Script" field
2. Add any required packages to the "Required Packages" list
3. Configure the timer as needed
4. Remove the old Nix expression

## Advanced Usage

For complex scenarios requiring advanced systemd configuration, you can combine the Bash Module with Custom Nix Modules or use environment variables passed from other modules.
