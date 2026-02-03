*** Comments ***
# Application Deployment Validation Suite
#
# This suite confirms that required applications are installed on Windows
# endpoints by querying the registry uninstall keys. It checks both the
# native (64-bit) and Wow6432Node (32-bit) registry hives so that
# applications installed under either architecture are detected.
#
# Registry paths queried:
#   HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*
#   HKLM:\Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*
#
# Each test searches for a DisplayName matching a pattern, extracts the
# DisplayVersion, and fails when the application cannot be found.
#
# Prerequisites:
#   - PowerShell 5.1+ (ships with Windows 10/11)
#   - No elevation required — the uninstall keys are world-readable

*** Settings ***
Documentation       Validates that required applications are installed by querying
...                 Windows registry uninstall keys. Reports the installed version
...                 for each application or fails if the application is missing.
Library             Process
Library             String
Library             Collections
Suite Setup         Log    Starting application deployment checks
Suite Teardown      Log    Application deployment checks complete

*** Variables ***
${POWERSHELL}       powershell.exe

# Registry paths for installed applications (64-bit and 32-bit)
${REG_UNINSTALL}        HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*
${REG_UNINSTALL_WOW}    HKLM:\\Software\\Wow6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*

# Search patterns — used as regex against DisplayName
${PATTERN_OFFICE}       Microsoft (Office|365|Word|Excel|PowerPoint)
${PATTERN_ACROBAT}      Adobe Acrobat
${PATTERN_7ZIP}         7-Zip
${PATTERN_CHROME}       Google Chrome

*** Keywords ***
Run PowerShell Command
    [Documentation]    Executes a PowerShell command and returns the result object.
    ...                Fails with a descriptive message on non-zero exit codes.
    [Arguments]    ${command}    ${fail_msg}=PowerShell command failed
    ${result}=    Run Process    ${POWERSHELL}
    ...    -NoProfile    -NonInteractive    -Command    ${command}
    IF    ${result.rc} != 0
        ${has_stderr}=    Evaluate    len($result.stderr.strip()) > 0
        ${error_detail}=    Set Variable If    ${has_stderr}
        ...    ${result.stderr}    (no stderr — rc ${result.rc})
        Fail    ${fail_msg}: ${error_detail}
    END
    RETURN    ${result}

Query Installed Application
    [Documentation]    Searches both 64-bit and 32-bit registry uninstall keys for an
    ...                application whose DisplayName matches the given regex pattern.
    ...                Returns a two-element list: [display_name, display_version].
    ...                Fails if the application is not found in either hive.
    [Arguments]    ${pattern}    ${app_label}
    # Build a single PowerShell script that searches both hives.
    # It outputs "DisplayName|||DisplayVersion" for the first match,
    # or "NOT_FOUND" when nothing matches.
    ${cmd}=    Catenate    SEPARATOR=\n
    ...    $paths = @(
    ...        '${REG_UNINSTALL}',
    ...        '${REG_UNINSTALL_WOW}'
    ...    )
    ...    foreach ($p in $paths) {
    ...        try {
    ...            $apps = Get-ItemProperty $p -ErrorAction SilentlyContinue |
    ...                Where-Object { $_.DisplayName -match '${pattern}' } |
    ...                Select-Object -First 1
    ...            if ($apps) {
    ...                $name = $apps.DisplayName
    ...                $ver  = if ($apps.DisplayVersion) { $apps.DisplayVersion } else { 'unknown' }
    ...                Write-Output "$name|||$ver"
    ...                exit 0
    ...            }
    ...        } catch {
    ...            continue
    ...        }
    ...    }
    ...    Write-Output 'NOT_FOUND'

    ${result}=    Run PowerShell Command    ${cmd}
    ...    fail_msg=Failed to query registry for ${app_label}

    ${output}=    Strip String    ${result.stdout}

    IF    "${output}" == "NOT_FOUND"
        Fail    ${app_label} is not installed — searched both 64-bit and 32-bit registry hives
    END

    # Split on the ||| delimiter
    @{parts}=    Split String    ${output}    |||
    ${name}=     Set Variable    ${parts}[0]
    ${version}=  Set Variable    ${parts}[1]

    Log    Found: ${name} (version ${version})    level=INFO
    RETURN    ${name}    ${version}

*** Test Cases ***
Microsoft Office Is Installed
    [Documentation]    Verifies that a Microsoft Office product (Word, Excel,
    ...                PowerPoint, or Microsoft 365) is present in the registry.
    ...                Any edition or version satisfies this check.
    [Tags]    office    productivity    required
    ${name}    ${version}=    Query Installed Application
    ...    ${PATTERN_OFFICE}    Microsoft Office
    Log    PASS — ${name} version ${version} is installed

Adobe Acrobat Reader Is Installed
    [Documentation]    Checks for Adobe Acrobat Reader (any version, including
    ...                Acrobat Reader DC and Acrobat Pro). PDF viewing capability
    ...                is required on all managed endpoints.
    [Tags]    adobe    pdf    required
    ${name}    ${version}=    Query Installed Application
    ...    ${PATTERN_ACROBAT}    Adobe Acrobat Reader
    Log    PASS — ${name} version ${version} is installed

7-Zip Is Installed
    [Documentation]    Confirms that 7-Zip is installed. 7-Zip is the approved
    ...                archive utility for handling compressed files.
    [Tags]    7zip    utility    required
    ${name}    ${version}=    Query Installed Application
    ...    ${PATTERN_7ZIP}    7-Zip
    Log    PASS — ${name} version ${version} is installed

Google Chrome Is Installed
    [Documentation]    Validates that Google Chrome is present. Chrome is the
    ...                supported browser for internal web applications.
    [Tags]    chrome    browser    required
    ${name}    ${version}=    Query Installed Application
    ...    ${PATTERN_CHROME}    Google Chrome
    Log    PASS — ${name} version ${version} is installed
