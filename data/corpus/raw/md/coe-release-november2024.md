## NOTES
- includes update to the kit for changes from PG around Audit Logs and HTTP Preauth connector.

## First Time Setup Instructions
- Get started with the CoE Starter Kit Setup: https://docs.microsoft.com/en-us/power-platform/guidance/coe/setup

## Upgrade Instructions
- Upgrading from the latest version of the CoE Starter Kit: https://docs.microsoft.com/power-platform/guidance/coe/after-setup

## Customizing the CoE Starter Kit
- Best practices on customizing and extending the CoE Starter Kit: https://docs.microsoft.com/en-us/power-platform/guidance/coe/modify-components

## Change Log
### 🐛 CoE Starter Kit - *BUGS* (16)
https://github.com/microsoft/coe-starter-kit/issues/7955 [CoE Starter Kit - BUG] DLP Request | Sync Policy to Dataverse (Child) Failing
https://github.com/microsoft/coe-starter-kit/issues/8864 [CoE Starter Kit - BUG] Blogs in CoE Admin Command App
https://github.com/microsoft/coe-starter-kit/issues/8966 Deal with System Owned flows
https://github.com/microsoft/coe-starter-kit/issues/8997 [CoE Starter Kit - BUG] Embedded PowerApp to manage apps/flows in PowerBI Dashboard does not work after August COE release
https://github.com/microsoft/coe-starter-kit/issues/8992 [CoE Starter Kit - BUG] COE Dashboard - App Shared With (Total) missing from model
https://github.com/microsoft/coe-starter-kit/issues/9042 [CoE Starter Kit - BUG] Compliance App Email always englisch
https://github.com/microsoft/coe-starter-kit/issues/9043 Accidentally deleting the spatial services connector in Delete Bad Data flow
https://github.com/microsoft/coe-starter-kit/issues/9101 [CoE Starter Kit - BUG] missing expression in a condition of Compliance Details Request eMail (Apps) flow cause HELPER - send mail to fail
https://github.com/microsoft/coe-starter-kit/issues/9109 [CoE Starter Kit - BUG] Typo in records created by HELP - Driver Escalation Check in Sync Flow Errors table
https://github.com/microsoft/coe-starter-kit/issues/9104 Connectors issue: http webhook v when http request received
https://github.com/microsoft/coe-starter-kit/issues/9120 [CoE Starter Kit - BUG] Assign new owner to orphaned app --> app still flaged as orphaned
https://github.com/microsoft/coe-starter-kit/issues/9121 [CoE Starter Kit - Feature]: Orphaned Process Assignment Fails Due to Manager Not Being Part of Environment Security Group
https://github.com/microsoft/coe-starter-kit/issues/9161 [CoE Starter Kit - BUG] Managed Permissions app not allowing search
https://github.com/microsoft/coe-starter-kit/issues/9172 [CoE Starter Kit - BUG] Power Platform Admin View app no longer allows you to change the owner of a flow or app
https://github.com/microsoft/coe-starter-kit/issues/9193 Product solution changes require fixes to the Setup Wizard
https://github.com/microsoft/coe-starter-kit/issues/9201 SYNC HELPER - Apps is clearing the shared with count

### 🎉 CoE Starter Kit - *FEATURES* (4)
https://github.com/microsoft/coe-starter-kit/issues/9118 [CoE Starter Kit - Feature]: Setup Wizard addition - check that required HTTP with Entra ID Scopes are all approved and working
https://github.com/microsoft/coe-starter-kit/issues/9144 Purvue schema changing - audit logs will need updated
https://github.com/microsoft/coe-starter-kit/issues/9169 Envt Keep Alive - we check for states (ex PCF) for all envts, even ones excused from inventory
https://github.com/microsoft/coe-starter-kit/issues/9190 [CoE Starter Kit - BUG] Sync Audit Logs V2 - Not Capturing all Audit Logs due to minimal delay