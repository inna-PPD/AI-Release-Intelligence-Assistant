# defects_github.jsonl

20 записів. Згенеровано з `defects_github.jsonl`, не редагуйте вручну.

---

## gh-001

`source: github` · `channel: github_issue` · `origin: microsoft/coe-starter-kit#10891`

Admin | Gather Tenant SRs -Action 'Delete_Removed_SRs_without_TIDs' failed

**Does this bug already exist in our backlog?**

**Describe the issue**

The 'inputs.parameters' of workflow operation 'Delete_Removed_SRs_without_TIDs' of type 'OpenApiConnection' is not valid. Error details: The resolved string values for the following parameters are invalid, they may not be null or empty: 'recordId'

**Expected Behavior**

_No response_

**What solution are you experiencing the issue with?**

Core

**What solution version are you using?**

4.50.9

**What app or flow are you having the issue with?**

Admin | Gather Tenant SRs

**What method are you using to get inventory and telemetry?**

Cloud flows

**Steps To Reproduce**

_No response_

**Anything else?**

No customization done in flow ,Failing every month post upgrade to 4.50.6 (Nov 25) upgrade.

[image]

[image]

[image]

---

## gh-002

`source: github` · `channel: github_issue` · `origin: microsoft/coe-starter-kit#11018`

[CoE Starter Kit - BUG] ISSUE TITLE - Old error received in two COE Flows

**Does this bug already exist in our backlog?**

**Describe the issue**

We are receiving an old error in two of the flows - 1. Admin | Sync Template V4 (Custom Connectors) - 98 times 
                                                                                 2. CLEANUP HELPER - Check Deleted V4 (Custom Connectors) - 95 times
Previously this error by fixed but now it is again occurring. Old ticket link - <URL>

Attaching the screenshot of the error message, please advice or share resolution steps 

[image]

**Expected Behavior**

_No response_

**What solution are you experiencing the issue with?**

Core

**What solution version are you using?**

4.50.0

**What app or flow are you having the issue with?**

Admin | Sync Template v4 (Custom Connectors), CLEANUP HELPER - Check Deleted v4 (Custom Connectors)

**What method are you using to get inventory and telemetry?**

Cloud flows

**Steps To Reproduce**

_No response_

**Anything else?**

_No response_

---

## gh-003

`source: github` · `channel: github_issue` · `origin: microsoft/coe-starter-kit#11030`

[CoE Starter Kit - BUG] Data Export stopped working for app data BYODL

**Does this bug already exist in our backlog?**

**Describe the issue**

We've had the CoE Starter Kit implemented with Azure Data Export for about a year, but have consistently faced problems with the data export. Initially, we noticed only delays, but now the App data, App connection data, and app connection references haven't been refreshed since March 13, 2026. All other data, such as flow data or usage data, are being refreshed within the officially communicated delay window. We've thoroughly checked the configuration and everything appears to be set up correctly. There are no error messages or failed runs reported in the Azure Data Export logs for the App data, App connection data, or app connection references. Despite our best efforts and extensive research, we have found no way to repair the issue or manually restart the data export.

**Expected Behavior**

Our main goal is to have the app data refreshed daily, ensuring our inventory stays current and that monitoring remains stable for all users.

**What solution are you experiencing the issue with?**

Core

**What solution version are you using?**

4.50.9

**What app or flow are you having the issue with?**

BYODL Azure Data Export

**What method are you using to get inventory and telemetry?**

Data Export

**Steps To Reproduce**

_No response_

**Anything else?**

_No response_

---

## gh-004

`source: github` · `channel: github_issue` · `origin: microsoft/coe-starter-kit#10851`

[CoE Starter Kit - BUG] Bad Gateway Env Request | Create Approved Environment Dataverse failure 

**Does this bug already exist in our backlog?**

**Describe the issue**

When creating a new environment request through the environment request maker page, I am faced with a 502 bad gateway when creating the Dataverse. It was previously working and nothing has changed. The app can no longer create environments .

It does create the environment without the dataverse after 4 hours of trying to create the Dataverse. 

**Update**: Same issue across multiple environments and latest CoE version, consistently 502 on ProvisionInstance

[image]

**Expected Behavior**

_No response_

**What solution are you experiencing the issue with?**

Core

**What solution version are you using?**

4.50.6

**What app or flow are you having the issue with?**

Env Request | Create Approved Environment

**What method are you using to get inventory and telemetry?**

None

**Steps To Reproduce**

_No response_

**Anything else?**

_No response_

---

## gh-005

`source: github` · `channel: github_issue` · `origin: microsoft/coe-starter-kit#10980`

8 Flows have failed with the same error message - "The user is not a member of the organization."

**Does this bug already exist in our backlog?**

**Describe the issue**

Current installed CoE starter Kit version: 4.5.0
Issue: The user is not a member of the organization.

We have identified that eight (8) Power Automate flows are consistently failing with the following error message:

"The user is not a member of the organization."

The affected flows and corresponding failing actions are listed below:
Admin | Sync Template v4

Desktop Flows – Action List_Envt_Desktop_Flows
Error: The user is not a member of the organization.
Model-Driven Apps – Action List_Envt_MDApps
Error: The user is not a member of the organization.
Canvas Apps – Action List_Envt_Apps
Error: The user is not a member of the organization.
Power Virtual Agents (PVA) – Action List_Envt_PVAs
Error: The user is not a member of the organization.
Business Process Flows – Action List_Envt_BPFs
Error: The user is not a member of the organization.

Cleanup Helper – Check Deleted v4

Solutions – Action List_Envt_Solutions
Error: The user is not a member of the organization.
Business Process Flows – Action List_Envt_BPFs
Error: The user is not a member of the organization.
Model-Driven Apps – Action List_Envt_MDAs
Error: The user is not a member of the organization.
Power Virtual Agents (PVA) – Action List_Envt_PVAs
Error: The user is not a member of the organization.

These failures are recurring and impacting the regular operation of our governance and cleanup automation processes.

We kindly request assistance in identifying the root cause of the membership-related error and providing guidance on resolving these failures. The flows are currently unable to run as expected.

[image]

**Expected Behavior**

_No response_

**What solution are you experiencing the issue with?**

Core

**What solution version are you using?**

4.50.0

**What app or flow are you having the issue with?**

Cleanup Helper – Check Deleted v4  ||  Admin | Sync Template v4

**What method are you using to get inventory and telemetry?**

None

**Steps To Reproduce**

_No response_

**Anything else?**

_No response_

---

## gh-006

`source: github` · `channel: github_issue` · `origin: microsoft/coe-starter-kit#10986`

[CoE Starter Kit - BUG] ISSUE TITLE

**Does this bug already exist in our backlog?**

**Describe the issue**

Previous ticket (Issue #10817)

[image]

Error Code: UserNotLoggedIn
Session Id: <GUID>
Activity Id: <GUID>
Timestamp: Thu Mar 26 2026 18:53:06 GMT+0530 (India Standard Time)
[AdalError] endpoints_resolution_error Error: could not resolve endpoints. Please check network and try again. Detail: ClientConfigurationError: untrusted_authority: The provided authority is not a trusted authority. Please include this authority in the knownAuthorities config parameter.
UciError: [AdalError] endpoints_resolution_error Error: could not resolve endpoints. Please check network and try again. Detail: ClientConfigurationError: untrusted_authority: The provided authority is not a trusted authority. Please include this authority in the knownAuthorities config parameter. at s (<URL> at <URL>

We already raised this issue with our network team and there is no SSL inspection happening.

Please schedule a call tomorrow i.e. 27th Mar at 5:30 PM IST where our Network team, Zscaler vendor is also available.

**Expected Behavior**

_No response_

**What solution are you experiencing the issue with?**

Core

**What solution version are you using?**

4.50.8

**What app or flow are you having the issue with?**

Center of Excellence - Core Components Apps

**What method are you using to get inventory and telemetry?**

None

**Steps To Reproduce**

[image]

**Anything else?**

Please add <EMAIL> and <EMAIL> while responding to the email.

[image]

---

## gh-007

`source: github` · `channel: github_issue` · `origin: microsoft/coe-starter-kit#10992`

[CoE Starter Kit - BUG] not receiving responses to created and assigned support tickets for several weeks

**Does this bug already exist in our backlog?**

**Describe the issue**

I have raised 2 support which have been assigned to an owner but none have received replies at all in over 4 weeks, I can see other users are having a similar issue

Examples:

<URL>
<URL>

**Expected Behavior**

Responses within a week usually

**What solution are you experiencing the issue with?**

Core

**What solution version are you using?**

N/A

**What app or flow are you having the issue with?**

N/A

**What method are you using to get inventory and telemetry?**

None

**Steps To Reproduce**

_No response_

**Anything else?**

_No response_

---

## gh-008

`source: github` · `channel: github_issue` · `origin: microsoft/coe-starter-kit#11013`

Admin | Audit Logs | Load events from exported Audit Log CSV file - The response is not in a JSON format.

**Does this bug already exist in our backlog?**

**Describe the issue**

When attempting to import the historical activity audit log .csv file from Purview i am met with a response of "The response is not in a JSON format".

[image]

My file is under 50,000 rows which is a known issue when trying to import the file.

Guidance document - <URL>

**Expected Behavior**

The flow to accept the .csv file and populate the solution for me to view historical audit data across PowerApps.

**What solution are you experiencing the issue with?**

Core

**What solution version are you using?**

4.50.9 (COE Core Components)

**What app or flow are you having the issue with?**

Admin | Audit Logs | Load events from exported Audit Log CSV file

**What method are you using to get inventory and telemetry?**

Cloud flows

**Steps To Reproduce**

Collect Purview Audit log data
Filter by "Launched App" as an activity filter
Export all of the results to a .csv file
Run the Admin | Audit Logs | Load events from exported Audit Log CSV file flow
Import the audit log .csv file on the flow

**Anything else?**

I noticed when i exported the "Launched App" activities from the purview audit log there is two items to choose from. Not sure if this is relevant or not.

[image]

I have ran and completed both the Setup Wizard - ARM Features and COE Setup and Upgrade Wizard

---

## gh-009

`source: github` · `channel: github_issue` · `origin: microsoft/coe-starter-kit#11019`

[CoE Starter Kit - BUG] Welcome Email feature not creating Admin | Welcome Email v3 flow via Setup & Upgrade Wizard

**Does this bug already exist in our backlog?**

**Describe the issue**

Admin | Welcome Email v3 flow is not being provisioned in a CoE environment running CenterOfExcellenceCoreComponents_4.50.9_managed.

Even after installing Core Components 4.50.9 and using the CoE Setup & Upgrade Wizard to enable “Welcome Email” under More features, the Admin | Welcome Email v3 flow does not appear in the environment.

**Expected Behavior**

**Expected Behavior**
After enabling Welcome Email via the CoE Setup & Upgrade Wizard, the solution should provision the Admin | Welcome Email v3 flow as documented under “Other Core Components”.

**Actual Behavior**
No Admin | Welcome Email v3 flow is created or visible in the environment.
There are no import failures or error messages.

**What solution are you experiencing the issue with?**

Core

**What solution version are you using?**

4.50.9

**What app or flow are you having the issue with?**

Admin | Welcome Email v3

**What method are you using to get inventory and telemetry?**

Cloud flows

**Steps To Reproduce**

1. Install CenterOfExcellenceCoreComponents_4.50.9_managed
2. Open CoE Setup & Upgrade Wizard
3. Navigate to More Features
4. Enable “Welcome Email”
5. Check Power Automate → Flows

[image]

[image]

**Anything else?**

The CoE Starter Kit download package does not contain a CenterOfExcellenceNurtureComponents_4.50.9_managed.zip, which makes it unclear how Welcome Email v3 dependencies are expected to be satisfied for Core 4.50.9.

---

## gh-010

`source: github` · `channel: github_issue` · `origin: microsoft/coe-starter-kit#10874`

[CoE Starter Kit - BUG] Out-of-date solution offered as "latest version" in documentation

**Does this bug already exist in our backlog?**

**Describe the issue**

The "latest version of the CoE Starter Kit" offered in the documentation for updating the COE is out of date.  The Core version in that download is 4.50.6, but we are now on version 4.50.9.  It seems to still be using the November release.  [<URL>

**Expected Behavior**

Clicking the "aka.ms/CoeStarterKitDownload" link in the documentation downloads the latest version of the CoE Starter Kit (from February).

**What solution are you experiencing the issue with?**

Core

**What solution version are you using?**

4.50.9

**What app or flow are you having the issue with?**

N/A

**What method are you using to get inventory and telemetry?**

Cloud flows

**Steps To Reproduce**

1. Go to [<URL>
2. Click the "CoeStarterKitDownload" link ("aka.ms/CoeStarterKitDownload").
3. Open the downloaded folder
4. Note the "CenterofExcellenceCoreComponents" solution version is 4.50.6 and most last modified dates are 10-28-25 or 11-4-25

**Anything else?**

_No response_

---

## gh-011

`source: github` · `channel: github_issue` · `origin: microsoft/powerplatform-build-tools#1089`

[pcf-1063] [Error] Unsupported 'React' version '16.14.0' specified platform-library.

**Describe the bug**
I'm trying to build PCFs using latest platform libraries as described in the ms docs [React controls & platform libraries](<URL> however I'm getting the following error. "[pcf-1063] [Error] Unsupported 'React' version '16.14.0' specified platform-library."

This is the package.json 
[package.json](<URL>
and controlManifest [ControlManifest.Input.txt](<URL>
of one of the projects that are failing to build.

**To Reproduce**
Steps to reproduce the behavior:
1. See **Screnshots**

**Expected behavior**
Successful compilation

**Screenshots**
`PS C:\Users\<USER>\source\Eos.PWA.PowerAppsTools_Eos\powercat-code-components\Solution> pac install latest
Feeds used:
  <URL>

Installing package 'Microsoft.PowerApps.CLI' to 'C:\Users\<USER>\AppData\Local\Microsoft\PowerAppsCLI'.
  GET <URL>
  OK <URL> 166ms
Pacchetto "Microsoft.PowerApps.CLI.1.38.3" è già installato
PS C:\Users\<USER>\source\Eos.PWA.PowerAppsTools_Eos\powercat-code-components\Solution> msbuild /t:build /restore /p:PcfBuildMode=production
Versione di MSBuild 17.12.6+db5f6012c per .NET Framework
Compilazione avviata 05/12/2024 11:25:50.

Progetto "C:\Users\<USER>\source\Eos.PWA.PowerAppsTools_Eos\powercat-code-components\Solution\Solution.cdsproj" sul n
odo 1 (destinazioni: Restore).
_GetAllRestoreProjectPathItems:
  Individuazione dei progetti da ripristinare...
Restore:
  La convalida della catena di certificati X.509 userà l'archivio attendibilità predefinito selezionato da .NET per la
  firma del codice.
  La convalida della catena di certificati X.509 userà l'archivio attendibilità predefinito selezionato da .NET per il
  timestamp.
  Il file di asset non è stato modificato. La scrittura sul file di asset verrà ignorata. Percorso: C:\Users\<USER>\s
  ource\Eos.PWA.PowerAppsTools_Eos\powercat-code-components\Solution\obj\project.assets.json
  Il file di asset non è stato modificato. La scrittura sul file di asset verrà ignorata. Percorso: C:\Users\<USER>\s
  ource\Eos.PWA.PowerAppsTools_Eos\powercat-code-components\Icon\obj\project.assets.json
  Il file di asset non è stato modificato. La scrittura sul file di asset verrà ignorata. Percorso: C:\Users\<USER>\s
  ource\Eos.PWA.PowerAppsTools_Eos\powercat-code-components\Spinner\obj\project.assets.json
  Il file di asset non è stato modificato. La scrittura sul file di asset verrà ignorata. Percorso: C:\Users\<USER>\s
  ource\Eos.PWA.PowerAppsTools_Eos\powercat-code-components\Nav\obj\project.assets.json
  Il file di asset non è stato modificato. La scrittura sul file di asset verrà ignorata. Percorso: C:\Users\<USER>\s
  ource\Eos.PWA.PowerAppsTools_Eos\powercat-code-components\Pivot\obj\project.assets.json
  Il file di asset non è stato modificato. La scrittura sul file di asset verrà ignorata. Percorso: C:\Users\<USER>\s
  ource\Eos.PWA.PowerAppsTools_Eos\powercat-code-components\DetailsList\obj\project.assets.json
  C:\Users\<USER>\s
[...]

---

## gh-012

`source: github` · `channel: github_issue` · `origin: microsoft/powerplatform-build-tools#1211`

pac catalog submit fails in v1.46.1 with Typeload exception "could not load file or assembly 'Microsoft.PowerPlatform.Dataverse.Client,"

Seems that the pac catalog submit command is broken in the latest pac cli version

I get a nasty type load exception. Tried it on an OOTB ADO build agent and on my local machine. Using the same command in v1.44.2 works like a charm. 

[image]

---

## gh-013

`source: github` · `channel: github_issue` · `origin: microsoft/powerplatform-build-tools#1438`

`pac package deploy` hangs indefinitely (deadlock) deploying X++/FnO external package to Unified Developer Experience (UDE) environment

**Describe the bug**
`pac package deploy` (Dataverse package-type, external `xpp` package) deadlocks indefinitely when deploying an X++/Finance and Operations module to a Unified Developer Experience (UDE) environment. The process never completes, never errors, and never times out. Confirmed via full process dump analysis: the main thread blocks forever on an internal `ManualResetEventSlim.Wait()` inside `pac`'s own deployment code, waiting for a signal that is never sent. All other threads in the process are completely idle — there is no background work in progress anywhere.

This is fully reproducible and independent of:
- The `pac` CLI version (reproduced identically on 2.10.1 and 2.8.1)
- The deployable package's content/structure (reproduced with both a hand-built package and one generated by Microsoft's own official Azure Pipelines "Create Deployable Package" (`XppCreatePackage@3`) task with "Create Power Platform Unified Package" enabled)

**Environment**

- `pac` CLI versions tested: 2.10.1+g52c3983 and 2.8.1+ga4eb71c (.NET Framework 4.8.9336.0, Windows build)
- Target environment: Unified Developer Experience (UDE)-provisioned Dataverse/Finance and Operations environment, provisioned via Power Platform Admin Center (no associated LCS project)
- Target org: Dataverse version 9.2.26072.138
- F&O environment: Platform 7.0.7858.134, Application 10.0.2527.160, Host Type "OnlineDev"
- Windows 11 (build 10.0.26100)

**To Reproduce**
Steps to reproduce the behavior:
1. Provision a UDE-linked F&O environment via Power Platform Admin Center (no LCS project).
2. Build an X++ model with custom table/field extensions in Visual Studio 2022 (Unified Developer Experience tooling). Confirm the model deploys successfully via **Extensions → Dynamics 365 → Deploy → Deploy Models to Online Environment** in Visual Studio (this path works correctly and is not affected by this bug).
3. Create a Dataverse "Package Deployer" project (`pac package init`) and add the X++ deployable package as an external package: `pac package add-external-package --package-type xpp --path <deployable-package.zip>`.
4. Build the project (`dotnet build`) to produce the package DLL and `PkgAssets/ImportConfig.xml`.
5. Ensure the referenced zip is a correctly-formed Power Platform Unified Package (containing `fnomoduledefinition.json` at the root plus the compiled model folder) — produced via the official Azure Pipelines `XppCreatePackage@3` task with `CreateCloudPackage: true`. (A package missing this structure fails fast and cleanly with a different, expected error — "Unable to find file named fnomoduledefinition.json inside zip" — that is not the subject of this report.)
6. Authenticate: `pac auth create --environment <env-url>`
7. Run: `pac package deploy --package <path-to-package.dll> --logConsole --verbose`

**Expected behavior**
The deployment
[...]

---

## gh-014

`source: github` · `channel: github_issue` · `origin: microsoft/powerplatform-build-tools#1160`

pac package deploy cmd missing

**Describe the bug**
I tend to use `pac package deploy` frequently. Without warning, today the cmd is gone. I get the following error when trying to run:

```
Microsoft PowerPlatform CLI
Version: 1.27.6+g9f62afb
Online documentation: <URL>
Feedback, Suggestions, Issues: <URL>
Error: The command 'deploy' is not understood in this context.

Usage: pac package [init] [add-external-package] [add-solution] [add-reference]

  init                        Initializes a directory with a new Dataverse package project
  add-external-package        Adds a package that is external to the Dataverse solution system to a Package Deployer Package project.
  add-solution                Adds a prebuilt Dataverse solution file to a Package Deployer Package project.
  add-reference               Adds reference to Dataverse solution project
```

**To Reproduce**
Steps to reproduce the behavior:
from the VS code terminal, run: `pac package deploy`

**Expected behavior**
expect `pac package deploy` to exist and deploy a package

**Desktop (please complete the following information):**
 - OS: Windows 11
 - Version 1.27.6+g9f62afb

**Additional context**
It appears there's something broken with the power apps VS code extension on my machine. I've tried updating the extension, I've uninstalled and reinstalled, I've restarted my machine, closed vs code... nothing seems to fix the fact it continues to show `v1.27.6` while my coworkers have much newer versions.

---

## gh-015

`source: github` · `channel: github_issue` · `origin: microsoft/powerplatform-build-tools#1254`

pac pcf push issue

**Bug Report**

**Describe the bug**
`pac pcf push` fails with a non-recoverable error when attempting to
push a PCF control to the Dataverse environment. The CLI throws
`System.UnauthorizedAccessException` and terminates.

**To Reproduce**
Steps to reproduce the behavior:
1. Open PowerShell in the PCF project folder: `C:\PCF_Calendar`
2. Run:
`powershell    pac pcf push --publisher-prefix exqaj3`
3. Observe the CLI output:
`Connected as <EMAIL>    Connected to... MyEnv    Using publisher prefix 'exqaj'.    Sorry, the app encountered a non recoverable error and will need to terminate.    Exception Type: System.UnauthorizedAccessException`
4. Command terminates without pushing the control.

**Expected behavior**
The CLI should create/update the temporary solution and successfully
push the PCF control to the Dataverse environment. The control should
then be available to add to forms/views.

**Screenshots**
N/A (see CLI output above).

**Desktop (please complete the following information):**
- **OS:** Windows (PowerShell)
- **Browser:** N/A (CLI operation)
- **PAC Version:** 1.43.6
- **Environment:** 
- **Publisher Prefix:** exqaj
- **User:** <EMAIL>

**Additional context**
- **Session Id:** `<GUID>`
- **Error Type:** `System.UnauthorizedAccessException`
- **Log file:**
`AppData\Local\Microsoft\PowerAppsCLI\Microsoft.PowerApps.CLI.1.43.6\tools\logs\pac-log.txt`
- Authentication succeeds but the push operation fails.
- Likely causes: insufficient Dataverse privileges, DLP restrictions, or
publisher mismatch.

---

## gh-016

`source: github` · `channel: github_issue` · `origin: microsoft/powerplatform-build-tools#1469`

Power Apps CLI package bug with complex object parameters

**Package**

- **Package:** `@microsoft/power-apps`
- **Version:** `1.3.0` (latest published)
- **Component:** Power Apps Code Apps, Dataverse connector data client
- **File:** `dist/internal/data/core/data/executors/dataverseDataOperationExecutor.js`
- **Function:** `toODataLiteral` (approximately line 803)

**Issue**

Generated Dataverse connector services fail when calling an OData function that accepts a complex or object-typed parameter.

One example is `RetrieveRecordChangeHistory`, which accepts:

- `Target` (`crmbaseentity`)
- `PagingInfo` (`PagingInfo`)

Calling the generated service returns the following Dataverse error:

```text
0x80060888: An unexpected StartArray node was found when reading from the JSON reader. A StartObject node was expected.
```

**Root Cause**

The issue appears to be in `toODataLiteral(value, type, format)`, which does not handle plain objects or complex types.

When an object is passed, the function falls through to:

```js
String(value)
```

which produces:

```text
[object Object]
```

As a result, Dataverse interprets the leading `[` as the start of a JSON array. Because the parameter is expected to be a JSON object, the Dataverse JSON reader throws a `StartArray` versus `StartObject` mismatch.

**Reproduction**

1. Generate a Power Apps Code Apps connector service for any Dataverse OData function that accepts a complex or object-typed parameter.
2. Call the generated service with a valid object value.
3. Observe that the request fails with error `0x80060888`, regardless of the object supplied.

**Expected Behavior**

Complex or object-typed parameters should be serialized as bare JSON object literals using `JSON.stringify(value)`, similar to how arrays are currently handled.

For example:

```js
if (type === 'object' && typeof value === 'object') {
    return JSON.stringify(value);
}
```

**Actual Behavior**

Objects are converted using:

```js
String(value)
```

which produces:

```text
[object Object]
```

This results in malformed OData parameter serialization and causes the Dataverse request to fail.

**Impact**

Any generated Dataverse connector service that invokes an OData function with a complex/object-typed parameter is unable to execute successfully. The failure occurs regardless of the contents of the supplied object, making these generated functions effectively unusable without patching the package.

**Workaround**

Patch `toODataLiteral` locally (for example, via `pnpm patch`) and add explicit handling for object types:

```js
if (type === 'object' && typeof value === 'object') {
    return JSON.stringify(value);
}
```

After applying this change, complex parameters are emitted correctly and Dataverse functions such as `RetrieveRecordChangeHistory` execute successfully.

---

## gh-017

`source: github` · `channel: github_issue` · `origin: microsoft/powerplatform-build-tools#1482`

`pac env fetch` doesn't output consistently

**Describe the bug**
Subsequent executions of the same `pac env fetch` command results in different outputs.

**To Reproduce**
Steps to reproduce the behavior:
1. Create an XML file (environment-variables.xml) with the following FetchXML query:
```xml

<fetch version='1.0' output-format='xml-platform' mapping='logical' distinct='true'>
    <entity name='environmentvariabledefinition'>
        <attribute name='schemaname' />
        <attribute name='defaultvalue' />
        <link-entity name='environmentvariablevalue' from='environmentvariabledefinitionid' to='environmentvariabledefinitionid' link-type='outer' alias='env'>
            <attribute name='value' />      
        </link-entity>
    </entity>
</fetch>
```
2. Execute the `fetch` command while referencing the XML file created in step 1: 
```
pac env fetch --xmlFile environment-variables.xml
```
3. Re-execute the command from step 2.
4. Note the columns and values that were output.

Sometimes, the columns / values are output as:
```
schemaname                                             defaultvalue
msdyn_SLAWebClientDeprecationAcknowledge               00
msdyn_ShouldShowPeekButton                             no
msdyn_lineofbusinessfiltertemplatefeatureuserexpansion 00000000-00000000-00000000-00000000
msdyn_lineofbusinessfiltertemplatefeature              00000000-00000000-00000000-00000000
```

Other times, it's output as:
```
schemaname                                             env.value
msdyn_SLAWebClientDeprecationAcknowledge               00
msdyn_ShouldShowPeekButton                             no
msdyn_lineofbusinessfiltertemplatefeatureuserexpansion 00000000-00000000-00000000-00000000
msdyn_lineofbusinessfiltertemplatefeature              00000000-00000000-00000000-00000000
```

**Expected behavior**
Results returned should respect the FetchXML query specified (column order and sorting).

**Desktop (please complete the following information):**
 - OS: Windows 11
 - Version: 2.11.2+g47bc199 (.NET Framework 4.8.9337.0)

**Additional context**
- The results aren't currently respecting the column ordering or sorting rules specified. 
- In some cases, columns are missing entirely.

---

## gh-018

`source: github` · `channel: github_issue` · `origin: microsoft/powerplatform-build-tools#1380`

Unable to download power pages site

**Describe the bug**
While trying to download power pages site code using pac cli, it errors out in GCC.

**To Reproduce**
Steps to reproduce the behavior:
1. Authenticate against the environment which has power pages site in GCC
2. Run 'pac pages list' to get websiteId
3. Run 'pac pages download -p 'c:\temp\site' -id '[websiteId]' - o
4. You will get 'Error: Power Pages entities aren't available on this org, please install Power Pages package on the org'.

**Expected behavior**
We should be able to download power pages site files.

**Screenshots**

[image]

**Desktop (please complete the following information):**
 - OS: Windows11
 - Version 2.7.4

**Additional context**
I am in GCC and this is happening for multiple site and for multiple users.

---

## gh-019

`source: github` · `channel: github_issue` · `origin: microsoft/powerplatform-build-tools#1374`

`pac solution pack` against YAML solution source incorrectly places Quick Create forms under `<forms type="quick" />`

**Describe the bug**
When running `pac solution pack` against a folder containing YAML generated by the Power Platform Git Integration that includes a table with a 'Quick Create' form, the resulting solution.zip file duplicates the Quick Create form definition under `<forms type='quick'>` as well as `<forms type='quickCreate'>`. 

This causes solution imports to fail when the quick create form contains an `<events />` definition.

**To Reproduce**
Steps to reproduce the behavior:
1. Create a solution, add a table and create a new Quick Create form 
2. Add an 'onLoad' event handler to the new Quick Create form
3. Use the Power Platform source control integration to commit the solution to git
4. Clone/download to git repository
5. Navigate to the solution root folder and run `pac solution pack --folder ./ --zipfile QuickCreateForm.zip --packageType managed` to generate an example.zip solution file
6. Attempt to import the example.zip managed solution file into another environment. An error will be shown stating _'Solution "QuickCreateForm" failed to import: Form XML of type quick with id <GUID> cannot contain element: events.'_
7. Manually unzip the QuickCreateForm.zip solution file and view the customizations.xml file. Observe that the `<forms type='quick'>` section contains a definition for the Quick Create form that includes `<events>`

**Expected behavior**
When packing YAML solution source, Quick Create form definitions should go under `<forms type='quickCreate'>` only.

**Screenshots**

customizations.xml showing the Quick Create form duplicated in `<forms type='quick' />` and `<forms type='quickCreate' />`

[image]

Error shown when importing solution:

[image]

**Desktop**
 - OS: Windows 11
- pac cli version 2.6.4

[image]

---

## gh-020

`source: github` · `channel: github_issue` · `origin: microsoft/powerplatform-build-tools#1224`

Plugin Registration Tool doesn't recognize environments in Sweden

**Describe the bug**
It seems the Plugin Registration Tool (started from `pac tool prt`) cannot list environments from Sweden (crm22).

**To Reproduce**
- Create new environment in Sweden
- Start prt: `pac tool prt`
- Choose to create a new connection

There is no alternative for "Sweden" among the regions. Moreover, choosing "Don't know" ignores all environments from region Sweden.

**Expected behavior**
I expect that either we can choose "Sweden" from the region dropdown, or choosing "Don't know" enumerates environments in Sweden as well.

Is there any way to make it find environments in crm22 as well?

**Screenshots**

[image]

Environments from other regions are enumerated correctly - here from crm4:

[image]

**Desktop (please complete the following information):**
 - OS: Windows 11
 - Browser: N/A
 - Version: 
    - PRT: 9.1.0.200, 
    - PowerPlatform CLI: 1.47.1+gc5a7855 (.NET Framework 4.8.9310.0)

**Additional context**

- The default environment is located in Europe (crm4) - if that is relevant.
- I am sysadmin in all environments, and power platform admin, I can log in to the environments without any problems
- It is possible to make PRT log in to a Swedish environment by setting the following key in the PluginRegistration.exe.config:

```
<add key="DirectConnectionUri" value="<URL> />
```

But I'd rather avoid having to change this manually each time ...
