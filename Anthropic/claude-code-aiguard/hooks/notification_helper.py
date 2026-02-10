#!/usr/bin/env python3
"""
Desktop notification helper for AI Guard hooks

Sends OS-level notifications when blocks occur so users in Cursor UI
can see why their request was blocked.
"""

import platform
import subprocess


def send_notification(title: str, message: str, sound: bool = True) -> bool:
    """
    Send desktop notification.

    Args:
        title: Notification title
        message: Notification message
        sound: Play sound with notification

    Returns:
        True if notification sent successfully, False otherwise
    """
    try:
        system = platform.system()

        if system == "Darwin":  # macOS
            # Use osascript for native macOS notifications
            sound_arg = 'sound name "Funk"' if sound else ""
            script = (
                f'display notification "{message}" with title "{title}" {sound_arg}'
            )
            subprocess.run(
                ["osascript", "-e", script], check=True, capture_output=True, timeout=2
            )
            return True

        elif system == "Linux":
            # Use notify-send on Linux
            urgency = "critical" if "BLOCKED" in title else "normal"
            subprocess.run(
                ["notify-send", "-u", urgency, title, message],
                check=True,
                capture_output=True,
                timeout=2,
            )
            return True

        elif system == "Windows":
            # Use PowerShell for Windows 10+ toast notifications
            ps_script = f'''
            [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null
            $Template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
            $RawXml = [xml] $Template.GetXml()
            ($RawXml.toast.visual.binding.text|where {{$_.id -eq "1"}}).AppendChild($RawXml.CreateTextNode("{title}")) > $null
            ($RawXml.toast.visual.binding.text|where {{$_.id -eq "2"}}).AppendChild($RawXml.CreateTextNode("{message}")) > $null
            $SerializedXml = New-Object Windows.Data.Xml.Dom.XmlDocument
            $SerializedXml.LoadXml($RawXml.OuterXml)
            $Toast = [Windows.UI.Notifications.ToastNotification]::new($SerializedXml)
            $Toast.Tag = "AIGuard"
            $Toast.Group = "AIGuard"
            $Notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Zscaler AI Guard")
            $Notifier.Show($Toast);
            '''
            subprocess.run(
                ["powershell", "-Command", ps_script],
                check=True,
                capture_output=True,
                timeout=2,
            )
            return True

    except Exception:
        # Fail silently - notifications are optional
        return False

    return False


def notify_block(severity: str, detectors: list, transaction_id: str = None):
    """
    Send notification for a blocked request.

    Args:
        severity: Block severity (CRITICAL, HIGH, MEDIUM, LOW)
        detectors: List of triggered detector names
        transaction_id: Optional transaction ID
    """
    icon = "🛑" if severity in ["CRITICAL", "HIGH"] else "⚠️"

    title = f"{icon} Zscaler AI Guard Blocked Request"

    if detectors:
        detectors_str = ", ".join(detectors[:3])  # Show max 3 detectors
        message = f"Severity: {severity}\nDetectors: {detectors_str}"
    else:
        message = f"Severity: {severity}\nPolicy violation detected"

    if transaction_id:
        # Truncate transaction ID for display
        short_txn = (
            transaction_id[:8] + "..." if len(transaction_id) > 8 else transaction_id
        )
        message += f"\nID: {short_txn}"

    send_notification(title, message, sound=True)


def notify_allow():
    """Send notification for an allowed request (optional, less intrusive)."""
    send_notification("✅ Zscaler AI Guard", "Request allowed", sound=False)


if __name__ == "__main__":
    # Test notifications
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        print("Testing desktop notifications...")

        # Test block notification
        success = notify_block(
            severity="CRITICAL",
            detectors=["credentials", "pii"],
            transaction_id="abc123-def456-ghi789",
        )

        if success:
            print("✅ Block notification sent successfully")
        else:
            print("❌ Failed to send notification (this is normal on some systems)")

    else:
        print("Usage:")
        print("  python notification_helper.py test   # Test notifications")
        print("")
        print("Or import in hooks:")
        print("  from notification_helper import notify_block")
        print("  notify_block('CRITICAL', ['credentials'], 'txn-123')")
