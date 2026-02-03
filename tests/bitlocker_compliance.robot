*** Comments ***
# BitLocker Compliance Test Suite
#
# This suite validates that Windows systems meet BitLocker encryption
# compliance requirements. It checks:
#   - BitLocker is enabled and fully encrypting the OS drive (C:)
#   - The encryption method meets the XTS-AES 256-bit standard
#   - The Trusted Platform Module (TPM) is initialized and ready
#   - UEFI Secure Boot is enabled
#
# Prerequisites:
#   - Must be run with Administrator privileges
#   - Windows 10/11 Pro, Enterprise, or Education edition
#   - TPM 2.0 hardware present
#
# PowerShell commands used:
#   Get-BitLockerVolume -MountPoint C:    (requires elevated privileges)
#   Get-Tpm                                (requires elevated privileges)
#   Confirm-SecureBootUEFI                 (requires UEFI firmware)

*** Settings ***
Documentation       BitLocker drive encryption compliance checks for Windows endpoints.
...                 Verifies encryption status, algorithm strength, TPM readiness,
...                 and Secure Boot configuration against organizational security policy.
Library             Process
Library             String
Suite Setup         Log    Starting BitLocker compliance checks — admin privileges required
Suite Teardown      Log    BitLocker compliance checks complete

*** Variables ***
${POWERSHELL}           powershell.exe
${MOUNT_POINT}          C:
${EXPECTED_ENCRYPTION}  XtsAes256

*** Keywords ***
Run PowerShell Command
    [Documentation]    Executes a PowerShell command and returns stdout/stderr/rc.
    ...                Fails the calling test with a clear message when the command
    ...                exits with a non-zero return code.
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

Get BitLocker Property
    [Documentation]    Queries a single property from Get-BitLockerVolume for the
    ...                configured mount point and returns the trimmed string value.
    [Arguments]    ${property}
    ${cmd}=    Set Variable
    ...    (Get-BitLockerVolume -MountPoint '${MOUNT_POINT}').${property}
    ${result}=    Run PowerShell Command    ${cmd}
    ...    fail_msg=Unable to query BitLocker property '${property}' — is BitLocker available on this edition of Windows?
    ${value}=    Strip String    ${result.stdout}
    RETURN    ${value}

*** Test Cases ***
BitLocker Is Enabled On OS Drive
    [Documentation]    Confirms that BitLocker protection is turned on for the C: drive.
    ...                The ProtectionStatus property returns "On" (1) when the volume
    ...                is actively protected and "Off" (0) when it is not.
    [Tags]    bitlocker    encryption    critical
    ${status}=    Get BitLocker Property    ProtectionStatus
    Should Be Equal As Strings    ${status}    On
    ...    msg=BitLocker protection is not enabled on ${MOUNT_POINT} (status: ${status})

Encryption Method Is XTS-AES 256
    [Documentation]    Verifies the encryption algorithm meets the XTS-AES 256-bit
    ...                requirement. Older or weaker methods (AES-128, AES-CBC) do
    ...                not satisfy the compliance policy.
    [Tags]    bitlocker    encryption    policy
    ${method}=    Get BitLocker Property    EncryptionMethod
    Should Be Equal As Strings    ${method}    ${EXPECTED_ENCRYPTION}
    ...    msg=Encryption method mismatch — expected ${EXPECTED_ENCRYPTION}, got '${method}'

Volume Is Fully Encrypted
    [Documentation]    Checks that encryption has completed across the entire volume.
    ...                A VolumeStatus of "FullyEncrypted" means no plaintext data
    ...                remains on disk. Statuses like "EncryptionInProgress" or
    ...                "FullyDecrypted" indicate non-compliance.
    [Tags]    bitlocker    encryption
    ${volume_status}=    Get BitLocker Property    VolumeStatus
    Should Be Equal As Strings    ${volume_status}    FullyEncrypted
    ...    msg=Volume is not fully encrypted — current status: ${volume_status}

TPM Is Initialized And Ready
    [Documentation]    Validates that the Trusted Platform Module (TPM) chip is
    ...                present, enabled, and ready for use. BitLocker in TPM mode
    ...                requires an initialized TPM. The Get-Tpm cmdlet returns
    ...                TpmPresent and TpmReady boolean properties.
    [Tags]    tpm    hardware    critical
    # Check TPM presence
    ${result_present}=    Run PowerShell Command
    ...    (Get-Tpm).TpmPresent
    ...    fail_msg=Unable to query TPM — is this system equipped with a TPM?
    ${tpm_present}=    Strip String    ${result_present.stdout}
    Should Be Equal As Strings    ${tpm_present}    True
    ...    msg=TPM is not present on this system

    # Check TPM readiness
    ${result_ready}=    Run PowerShell Command
    ...    (Get-Tpm).TpmReady
    ...    fail_msg=Unable to query TPM readiness
    ${tpm_ready}=    Strip String    ${result_ready.stdout}
    Should Be Equal As Strings    ${tpm_ready}    True
    ...    msg=TPM is present but not initialized (TpmReady: ${tpm_ready})

Secure Boot Is Enabled
    [Documentation]    Confirms that UEFI Secure Boot is active. Secure Boot prevents
    ...                unsigned or tampered bootloaders from executing, which protects
    ...                the BitLocker trust chain. Confirm-SecureBootUEFI returns True
    ...                when enabled, False when disabled, and throws on legacy BIOS.
    [Tags]    secureboot    uefi    critical
    ${result}=    Run PowerShell Command
    ...    Confirm-SecureBootUEFI
    ...    fail_msg=Unable to query Secure Boot — system may use legacy BIOS instead of UEFI
    ${secure_boot}=    Strip String    ${result.stdout}
    Should Be Equal As Strings    ${secure_boot}    True
    ...    msg=Secure Boot is not enabled (returned: ${secure_boot})
