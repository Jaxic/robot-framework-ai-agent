*** Comments ***
# Windows Critical Services Validation Suite
#
# This suite confirms that critical Windows services are present and
# running. A stopped or missing service indicates a misconfigured
# endpoint or a potential security gap.
#
# Services checked:
#   WinDefend / WdNisSvc  — Windows Defender Antivirus
#   wuauserv              — Windows Update
#   Dnscache              — DNS Client
#   mpssvc                — Windows Defender Firewall
#   W32Time               — Windows Time
#
# PowerShell commands used:
#   Get-Service -Name <ServiceName> -ErrorAction SilentlyContinue
#
# Prerequisites:
#   - PowerShell 5.1+ (ships with Windows 10/11)
#   - No elevation required for reading service status

*** Settings ***
Documentation       Validates that critical Windows services are installed and
...                 running. Each test queries a specific service by name, verifies
...                 its status, and reports the display name. A final summary test
...                 aggregates the state of all monitored services.
Library             Process
Library             String
Library             Collections
Suite Setup         Log    Starting critical Windows services checks
Suite Teardown      Log    Critical Windows services checks complete

*** Variables ***
${POWERSHELL}       powershell.exe

# Service names to validate (used by the summary test)
@{CRITICAL_SERVICES}    WinDefend    WdNisSvc    wuauserv    Dnscache    mpssvc    W32Time

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

Get Service Info
    [Documentation]    Queries a Windows service by name and returns its display name
    ...                and status as a two-element list. Outputs "NOT_FOUND" when the
    ...                service does not exist on this system.
    [Arguments]    ${service_name}
    ${cmd}=    Set Variable
    ...    $svc \= Get-Service -Name '${service_name}' -ErrorAction SilentlyContinue; if ($svc) { Write-Output "$($svc.DisplayName)|||$($svc.Status)" } else { Write-Output 'NOT_FOUND' }
    ${result}=    Run PowerShell Command    ${cmd}
    ...    fail_msg=Failed to query service '${service_name}'
    ${output}=    Strip String    ${result.stdout}
    RETURN    ${output}

Service Should Be Running
    [Documentation]    Asserts that a Windows service exists and is in the Running
    ...                state. Logs the display name on success, provides a clear
    ...                failure message otherwise.
    [Arguments]    ${service_name}    ${friendly_name}
    ${output}=    Get Service Info    ${service_name}
    IF    "${output}" == "NOT_FOUND"
        Fail    ${friendly_name} (${service_name}) — service not found on this system
    END
    @{parts}=    Split String    ${output}    |||
    ${display_name}=    Set Variable    ${parts}[0]
    ${status}=          Set Variable    ${parts}[1]
    Log    Service: ${display_name} — Status: ${status}    level=INFO
    Should Be Equal As Strings    ${status}    Running
    ...    msg=${friendly_name} (${display_name}) is ${status} — expected Running

Check Any Service Running
    [Documentation]    Checks whether at least one service from a list of names is
    ...                found and running. Returns the display name and status of
    ...                the first running match. Fails if none are running.
    [Arguments]    @{service_names}    ${friendly_name}=Service
    FOR    ${name}    IN    @{service_names}
        ${output}=    Get Service Info    ${name}
        IF    "${output}" != "NOT_FOUND"
            @{parts}=    Split String    ${output}    |||
            ${display_name}=    Set Variable    ${parts}[0]
            ${status}=          Set Variable    ${parts}[1]
            IF    "${status}" == "Running"
                Log    Service: ${display_name} — Status: ${status}    level=INFO
                RETURN    ${display_name}    ${status}
            END
        END
    END
    Fail    ${friendly_name} — none of the expected services (@{service_names}) are running

*** Test Cases ***
Windows Defender Antivirus Is Running
    [Documentation]    Checks that Windows Defender is active. The antivirus engine
    ...                can run under either the WinDefend service (main antimalware)
    ...                or WdNisSvc (network inspection). At least one must be running.
    [Tags]    defender    security    critical
    ${name}    ${status}=    Check Any Service Running
    ...    WinDefend    WdNisSvc
    ...    friendly_name=Windows Defender Antivirus
    Log    PASS — ${name} is ${status}

Windows Update Service Is Running
    [Documentation]    Confirms the Windows Update service (wuauserv) is running.
    ...                This service is required for receiving security patches and
    ...                feature updates from Microsoft.
    [Tags]    update    patching    critical
    Service Should Be Running    wuauserv    Windows Update

DNS Client Is Running
    [Documentation]    Verifies the DNS Client service (Dnscache) is active. This
    ...                service caches DNS lookups and is essential for name
    ...                resolution on the network.
    [Tags]    dns    networking    required
    Service Should Be Running    Dnscache    DNS Client

Windows Firewall Is Running
    [Documentation]    Checks that the Windows Defender Firewall service (mpssvc) is
    ...                running. The firewall filters inbound and outbound traffic
    ...                based on configured rules.
    [Tags]    firewall    security    critical
    Service Should Be Running    mpssvc    Windows Firewall

Windows Time Service Is Running
    [Documentation]    Validates that the Windows Time service (W32Time) is active.
    ...                Accurate time synchronization is required for Kerberos
    ...                authentication, TLS certificate validation, and audit logging.
    [Tags]    time    ntp    required
    Service Should Be Running    W32Time    Windows Time

Critical Services Summary
    [Documentation]    Aggregates the status of all monitored services into a single
    ...                report. Lists each service as Running, Stopped, or Not Found.
    ...                Fails if any critical service is not running.
    [Tags]    summary    report
    @{running}=     Create List
    @{not_running}=    Create List

    FOR    ${svc}    IN    @{CRITICAL_SERVICES}
        ${output}=    Get Service Info    ${svc}
        IF    "${output}" == "NOT_FOUND"
            Append To List    ${not_running}    ${svc} (Not Found)
            Log    MISSING — ${svc} not found on this system    level=WARN
        ELSE
            @{parts}=    Split String    ${output}    |||
            ${display_name}=    Set Variable    ${parts}[0]
            ${status}=          Set Variable    ${parts}[1]
            IF    "${status}" == "Running"
                Append To List    ${running}    ${display_name} (${svc})
                Log    OK — ${display_name} is Running    level=INFO
            ELSE
                Append To List    ${not_running}    ${display_name} (${svc}) — ${status}
                Log    PROBLEM — ${display_name} is ${status}    level=WARN
            END
        END
    END

    ${running_count}=       Get Length    ${running}
    ${not_running_count}=   Get Length    ${not_running}
    ${total}=    Evaluate    ${running_count} + ${not_running_count}

    Log    \n===== CRITICAL SERVICES SUMMARY =====    level=INFO
    Log    Running: ${running_count} / ${total}    level=INFO
    FOR    ${entry}    IN    @{running}
        Log    \ \ [Running] ${entry}    level=INFO
    END
    FOR    ${entry}    IN    @{not_running}
        Log    \ \ [PROBLEM] ${entry}    level=WARN
    END
    Log    ======================================    level=INFO

    IF    ${not_running_count} > 0
        Fail    ${not_running_count} critical service(s) not running: @{not_running}
    END
