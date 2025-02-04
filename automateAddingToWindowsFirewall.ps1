# Define the URL of the data endpoint
$dataUrl = "Fill this out with your endpoint"

# Define the group name for the firewall rules
$ruleGroupName = "AutoBlockedIPs"

# Fetch data from the endpoint
$jsonData = Invoke-RestMethod -Uri $dataUrl

# Loop through each item in the JSON data
foreach ($item in $jsonData) {
    # Check if the ipv4 field is not null
    if ($item.ipv4 -ne $null) {
        # Define the rule name based on the item id
        $ruleName = "Block_" + $item.id

        # Create a new firewall rule to block the IPv4 address and assign it to a group
        New-NetFirewallRule -DisplayName $ruleName `
            -Direction Inbound `
            -Action Block `
            -RemoteAddress $item.ipv4 `
            -Protocol TCP `
            -Profile Any `
            -Group $ruleGroupName `
            -Description "Automatically blocked due to security feed."
        Write-Output "Created firewall rule for IPv4: $($item.ipv4)"
    }
    else {
        Write-Output "No IPv4 address found for item ID: $($item.id)"
    }
}

# Example to disable all rules in the group
# Disable-NetFirewallRule -Group $ruleGroupName

# Example to enable all rules in the group
# Enable-NetFirewallRule -Group $ruleGroupName

# Example to remove all rules in the group
# Remove-NetFirewallRule -Group $ruleGroupName
