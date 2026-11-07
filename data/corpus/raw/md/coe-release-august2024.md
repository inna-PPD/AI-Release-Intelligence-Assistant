## NOTES
- Due to the below around AI Events flow we will release August now. However sovereign clouds will not be able to install until the new connector is supported there. 
- If you are a regular (commercial) tenant then you can feel free to begin to install this new build

## REGENERATED CORE on 8.15.24 to 4.37
Note that there was a COGS escalation and it was found that we had debug code in the Admin | Sync Template v4 (AI Events) flow which caused us to process 45 days worth of AI Events each day. So we had to recreate Core to resolve this. 
Please see https://github.com/microsoft/coe-starter-kit/issues/8814
New version of Core is now 4.37

## First Time Setup Instructions
- Get started with the CoE Starter Kit Setup: https://docs.microsoft.com/en-us/power-platform/guidance/coe/setup

## Upgrade Instructions
- Upgrading from the latest version of the CoE Starter Kit: https://docs.microsoft.com/power-platform/guidance/coe/after-setup

## Customizing the CoE Starter Kit
- Best practices on customizing and extending the CoE Starter Kit: https://docs.microsoft.com/en-us/power-platform/guidance/coe/modify-components

## Change Log
### 🐛 CoE Starter Kit - *BUGS* (18)
https://github.com/microsoft/coe-starter-kit/issues/8549 [CoE Starter Kit - QUESTION] Deleting Solution Aware Flows in CoE 
https://github.com/microsoft/coe-starter-kit/issues/8573 [CoE Starter Kit - BUG] Blogs in CoE Admin Command App
https://github.com/microsoft/coe-starter-kit/issues/8607 [CoE Starter Kit - BUG] Update naming convention DLP > Data Policies
https://github.com/microsoft/coe-starter-kit/issues/8611 Error on load admin command center bookmarks page: The value 'Preview builds for testing' cannot be converted to a date or time value
https://github.com/microsoft/coe-starter-kit/issues/8612 [CoE Starter Kit - BUG] ISSUE TITLE Admin | Newsletter with Product Updates flow, List Flow Blog RSS feed items fails
https://github.com/microsoft/coe-starter-kit/issues/8626 [CoE Starter Kit - BUG] Comments doesn't work when enabled along with Related videos
https://github.com/microsoft/coe-starter-kit/issues/8627 Fix reference to "preview" in command center support page
https://github.com/microsoft/coe-starter-kit/issues/8644 Maker Environment Request App - Least Privilege Security Principle
https://github.com/microsoft/coe-starter-kit/issues/8668 [CoE Starter Kit - BUG] AI Credits Usage table not added to CoE SR's
https://github.com/microsoft/coe-starter-kit/issues/8683 [CoE Starter Kit - BUG] Get_toWhom_profileo issue with the "Assign to all" button in the Request Orphaned Objects Reassigned (Child) flow
https://github.com/microsoft/coe-starter-kit/issues/8692 App Catalog and search bug 
https://github.com/microsoft/coe-starter-kit/issues/8697 [CoE Starter Kit - BUG] Wrong email sent to managers from Orphaned Objects "Email Me" option
https://github.com/microsoft/coe-starter-kit/issues/8711 [CoE Starter Kit - QUESTION] governance flows - import as disabled
https://github.com/microsoft/coe-starter-kit/issues/8724 [CoE Starter Kit - BUG] Maker Not Notified of Rejected Environment Request - Flow "Env Request | Notify requestor when rejected" Not Triggered
https://github.com/microsoft/coe-starter-kit/issues/8728 Failure in CLEANUP - Admin | Sync Template v3 (Orphaned Users) when cannot get tenant count
https://github.com/microsoft/coe-starter-kit/issues/8738 [CoE Starter Kit - BUG] Manage Permissions App fails when trying to delete orphaned flows
https://github.com/microsoft/coe-starter-kit/issues/8741 Environment Capacity for no Dataverse environment doesn't have capacity
https://github.com/microsoft/coe-starter-kit/issues/8776 [CoE Starter Kit - BUG] Video thumbnails not showing in MDA Video Hub New
https://github.com/microsoft/coe-starter-kit/issues/8729 Admin | Sync Template v4 (AI Events) failing - some users azureid not listed
https://github.com/microsoft/coe-starter-kit/issues/8814 Admin | Sync Template v4 (AI Events) consuming too many api calls due to debug code left in call
https://github.com/microsoft/coe-starter-kit/issues/8809 [CoE Starter Kit - QUESTION] Fix up spots that still have the removed "Total Shared With" field

### 🎉 CoE Starter Kit - *FEATURES* (8)
https://github.com/microsoft/coe-starter-kit/issues/8016 [CoE Starter Kit - Feature]: Update Kit to respond to new Power Platform Admin Role PIM feature
https://github.com/microsoft/coe-starter-kit/issues/8481 [CoE Starter Kit - Feature]: BVA Setup Wizard screen and Metadata integration
https://github.com/microsoft/coe-starter-kit/issues/8482 [CoE Starter Kit - Feature]: Integrate new audit log methodology into the kit for API reduction
https://github.com/microsoft/coe-starter-kit/issues/8565 [CoE Starter Kit - Feature]: Automated Install Roadmap
https://github.com/microsoft/coe-starter-kit/issues/8591 [CoE Starter Kit - Feature]: Automated Install - Setup Wizard - Connection consent
https://github.com/microsoft/coe-starter-kit/issues/8701 Add new TeamsWebhook specialty connector to the kit
https://github.com/microsoft/coe-starter-kit/issues/8716 [CoE Starter Kit - Feature]: PBI Dashboards - Production_CoEDashboard - Flow Deep Dive Page
https://github.com/microsoft/coe-starter-kit/issues/8752 PIM - only record escalation error after checking

